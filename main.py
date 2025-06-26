import time
import JSSEnv
import argparse
import numpy as np
import pandas as pd
import seaborn as sns
import gymnasium as gym
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Dict, List, Tuple, Any

import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning)

class ControllerJSSAgent:
    """JSS Agent that respects controller constraints for people-machine assignments"""
    
    def __init__(self, instance_path: str, controller_path: str, num_people: int):
        self.name = "ControllerJSSAgent"
        self.env = gym.make('jss-v1', env_config={'instance_path': instance_path})
        self.controller = self._load_controller(controller_path)
        self.num_people = num_people
        self.people_assignments = {}
        
    def _load_controller(self, controller_path: str) -> Dict[int, List[int]]:
        """Load controller file mapping people to allowed machines"""
        controller = {}
        with open(controller_path, 'r') as f:
            for line in f:
                parts = list(map(int, line.strip().split()))
                person_id = parts[0]
                allowed_machines = parts[1:]
                controller[person_id] = allowed_machines
        return controller
    
    def _get_available_people(self, machine_id: int, current_time: float) -> List[int]:
        """Get list of people who can use the specified machine and are available"""
        available = []
        for person_id, allowed_machines in self.controller.items():
            if machine_id in allowed_machines:
                # Check if person is not currently assigned to another machine
                if person_id not in self.people_assignments or \
                self.people_assignments[person_id]['end_time'] <= current_time:
                    available.append(person_id)
        return available
    
    def __call__(self, env, obs: Dict[str, np.ndarray]) -> int:
        """Select action considering controller constraints"""
        if isinstance(obs, dict) and "action_mask" in obs:
            legal_actions = obs["action_mask"]
        else:
            legal_actions = env.get_legal_actions()
        
        # Validate legal_actions size
        expected_action_size = env.jobs + 1  # jobs plus no-op
        if len(legal_actions) != expected_action_size:
            print(f"Error: legal_actions size {len(legal_actions)} does not match expected {expected_action_size}")
            return env.jobs
        
        # Get legal job indices with remaining operations and available people
        current_time = env.current_time_step
        legal_job_indices = []
        selected_person_for_job = {}
        
        for i in range(env.jobs):
            if legal_actions[i] and env.todo_time_step_job[i] < env.machines:
                current_op = env.todo_time_step_job[i]
                machine_id = env.instance_matrix[i][current_op][0]
                available_people = self._get_available_people(machine_id, current_time)
                if available_people:
                    legal_job_indices.append(i)
                    selected_person_for_job[i] = available_people[0]
        
        # If no valid jobs with available people, return no-op
        if not legal_job_indices:
            return env.jobs if legal_actions[env.jobs] else 0
        
        # Calculate scores for each legal job
        job_scores = {}
        for job_idx in legal_job_indices:
            current_op = env.todo_time_step_job[job_idx]
            machine_id = env.instance_matrix[job_idx][current_op][0]
            proc_time = env.instance_matrix[job_idx][current_op][1]
            
            # Calculate composite score
            score = self._calculate_job_score(env, job_idx, current_time)
            job_scores[job_idx] = score
        
        # Select best job
        best_job = max(job_scores.keys(), key=lambda x: job_scores[x])
        
        # Assign person to the selected job
        current_op = env.todo_time_step_job[best_job]
        machine_id = env.instance_matrix[best_job][current_op][0]
        proc_time = env.instance_matrix[best_job][current_op][1]
        selected_person = selected_person_for_job[best_job]
        
        self.people_assignments[selected_person] = {
            'machine_id': machine_id,
            'end_time': current_time + proc_time
        }
        
        return best_job
    
    def _calculate_job_score(self, env, job_idx: int, current_time: float) -> float:
        """Calculate composite score for a job"""
        current_op = env.todo_time_step_job[job_idx]
        proc_time = env.instance_matrix[job_idx][current_op][1]
        machine_id = env.instance_matrix[job_idx][current_op][0]
        
        # SPT score (Shortest Processing Time)
        spt_score = 1.0 - (proc_time / env.max_time_op) if env.max_time_op > 0 else 1.0
        
        # Work remaining score
        remaining_work = sum(env.instance_matrix[job_idx][op][1] 
                            for op in range(current_op + 1, env.machines))
        work_remaining_score = remaining_work / (env.max_time_op * env.machines) if env.max_time_op > 0 else 0.0
        
        # Machine availability score
        machine_available_time = env.time_until_available_machine[machine_id]
        machine_util_score = 1.0 - (machine_available_time / env.max_time_op) if env.max_time_op > 0 else 1.0
        
        # Person availability score
        available_people = self._get_available_people(machine_id, current_time)
        person_availability_score = len(available_people) / self.num_people if self.num_people > 0 else 0.0
        
        # Critical path score (new)
        earliest_start = max(current_time, machine_available_time)
        critical_path_score = 1.0 - (earliest_start / env.max_time_op) if env.max_time_op > 0 else 1.0
        
        # Dynamic weights
        weights = {
            'spt': 0.25,
            'work_remaining': 0.2,
            'machine_util': 0.25,
            'person_availability': 0.2,
            'critical_path': 0.1
        }
        
        return (weights['spt'] * spt_score +
                weights['work_remaining'] * work_remaining_score +
                weights['machine_util'] * machine_util_score +
                weights['person_availability'] * person_availability_score +
                weights['critical_path'] * critical_path_score)

    def run_episode(self) -> Tuple[float, float, List[Tuple[int, int, float, float, int]]]:
        """Run a single episode and collect scheduling information"""
        schedule = []  # Store (job_id, machine_id, start_time, end_time, person_id)
        obs, _ = self.env.reset()
        done = False
        total_reward = 0
        completed_ops = {i: set() for i in range(self.env.jobs)}  # Track completed operations per job
        
        
        while not done:
            action = self.__call__(self.env, obs)
            
            # Validate action
            if action >= self.env.jobs and action != self.env.jobs:
                print(f"Error: Invalid action {action} received, defaulting to no-op")
                action = self.env.jobs
            elif action < self.env.jobs and self.env.todo_time_step_job[action] >= self.env.machines:
                print(f"Error: Attempted to schedule completed job {action}, defaulting to no-op")
                action = self.env.jobs
            
            step_result = self.env.step(action)
            
            if len(step_result) == 5:
                obs, reward, done, truncated, _ = step_result
            else:
                obs, reward, done, _ = step_result
                truncated = False
                
            total_reward += reward
            
            # Record scheduling decision only for non-no-op actions
            if action < self.env.jobs:  # Not a no-op
                current_op = self.env.todo_time_step_job[action]
                if current_op < self.env.machines and (action, current_op) not in completed_ops[action]:
                    machine_id = self.env.instance_matrix[action][current_op][0]
                    proc_time = self.env.instance_matrix[action][current_op][1]
                    start_time = self.env.current_time_step
                    end_time = start_time + proc_time
                    
                    # Find which person was assigned
                    person_id = None
                    for pid, assignment in self.people_assignments.items():
                        if assignment['machine_id'] == machine_id and \
                        assignment['end_time'] >= end_time:
                            person_id = pid
                            break
                    
                    if person_id is not None:
                        schedule.append((action, machine_id, start_time, end_time, person_id))
                        completed_ops[action].add((action, current_op))
                    else:
                        print(f"Warning: No person assigned for job {action}, machine {machine_id}, skipping schedule entry")
            
            if truncated:
                done = True
        
        makespan = self.env.current_time_step
        print(f"Schedule contains {len(schedule)} tasks")
        return makespan, total_reward, schedule

def create_gantt_chart(schedule: List[Tuple[int, int, float, float, int]], 
                      save_path: str = "results/gantt_chart.png"):
    """Create a Gantt chart for the schedule"""
    plt.style.use('seaborn-v0_8-whitegrid')
    sns.set_palette("husl")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Prepare data for Gantt chart
    machines = sorted(list(set(task[1] for task in schedule)))
    colors = sns.color_palette("husl", n_colors=len(set(task[0] for task in schedule)))
    
    for task in schedule:
        job_id, machine_id, start_time, end_time, person_id = task
        duration = end_time - start_time
        machine_idx = machines.index(machine_id)
        
        # Plot task bar
        ax.barh(machine_idx, duration, left=start_time, height=0.4, 
                color=colors[job_id % len(colors)], 
                edgecolor='black', alpha=0.8)
    
    # Customize plot
    ax.set_yticks(range(len(machines)))
    ax.set_yticklabels([f'Machine {m}' for m in machines])
    ax.set_xlabel('Time')
    ax.set_ylabel('Machines')
    ax.set_title('JSS Gantt Chart')
    ax.grid(True, alpha=0.3)
    
    # Add legend
    job_patches = [mpatches.Patch(color=colors[i % len(colors)], 
                                 label=f'Job {i}') for i in range(len(colors))]
    plt.legend(handles=job_patches, bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    
    # Save the chart
    Path(save_path).parent.mkdir(exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Gantt chart saved to {save_path}")

def main():
    if not os.path.exists("results"):
        os.makedirs("results")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Job Shop Scheduling with Controller Constraints')
    parser.add_argument('--instance', type=str, default='dmu16', 
                       help='Instance name (default: dmu16)')
    parser.add_argument('--controller', type=str, default='20p_20m',
                       help='Controller name (default: 20p_20m)')
    parser.add_argument('--num_people', type=int, default=20,
                       help='Number of people (default: 20)')
    
    args = parser.parse_args()
    
    # Configuration using parsed arguments
    instance_name = args.instance
    instance_path = "instances/" + instance_name 
    controller_name = args.controller
    controller_path = "controllers/" + controller_name + ".txt"
    num_people = args.num_people
    result_path = "results/" + instance_name + "_" + controller_name + time.strftime("_%Y%m%d_%H%M%S") + "/"
    
    # Create result directory
    Path(result_path).mkdir(exist_ok=True)
    
    # Initialize agent
    agent = ControllerJSSAgent(instance_path, controller_path, num_people)
    
    # Run episode
    print("Running JSS with controller constraints...")
    makespan, total_reward, schedule = agent.run_episode()
    
    # Print results
    print(f"\nResults:")
    print(f"Makespan: {makespan:.2f}")
    print(f"Total Reward: {total_reward:.2f}")
    
    # Create Gantt chart
    create_gantt_chart(schedule, f"{result_path}gantt_chart.png")
    
    # Save detailed schedule
    schedule_df = pd.DataFrame(schedule, 
                             columns=['Job_ID', 'Machine_ID', 'Start_Time', 'End_Time', 'Person_ID'])
    schedule_df.to_csv(f"{result_path}schedule.csv", index=False)
    print(f"Detailed schedule saved to {result_path}schedule.csv")

if __name__ == "__main__":
    main()