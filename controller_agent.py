"""
Controller JSS Agent Implementation
"""

import numpy as np
import gymnasium as gym
from typing import Dict, List, Tuple

class ControllerJSSAgent:
    """JSS Agent that respects controller constraints for people-machine assignments"""

    def __init__(self, instance_path: str, controller_path: str, num_people: int):
        self.name = "ControllerJSSAgent"
        self.env = gym.make(
            'jss-v1', env_config={'instance_path': instance_path})
        self.controller = self._load_controller(controller_path)
        self.num_people = num_people
        self.people_assignments = {}
        # Add safeguards for performance
        self.last_action_time = 0
        self.consecutive_no_ops = 0
        self.max_consecutive_no_ops = 5  # Prevent excessive waiting

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

    def _get_earliest_available_person(self, machine_id: int, current_time: float) -> Tuple[int, float]:
        """Get the person who can use the machine and will be available earliest"""
        qualified_people = []
        for person_id, allowed_machines in self.controller.items():
            if machine_id in allowed_machines:
                if person_id not in self.people_assignments:
                    # Person is currently available
                    qualified_people.append((person_id, current_time))
                else:
                    # Person will be available at end_time
                    available_time = max(current_time, self.people_assignments[person_id]['end_time'])
                    qualified_people.append((person_id, available_time))
        
        if not qualified_people:
            # Provide detailed error information for debugging
            all_people = list(self.controller.keys())
            machine_assignments = {pid: machines for pid, machines in self.controller.items() if machine_id in machines}
            raise ValueError(f"No qualified people found for machine {machine_id}. "
                           f"Available people: {all_people}, "
                           f"People qualified for machine {machine_id}: {list(machine_assignments.keys())}")
        
        # Return person who will be available earliest
        return min(qualified_people, key=lambda x: x[1])

    def _find_best_person_machine_combination(self, env, job_idx: int, current_time: float) -> Tuple[int, float, float]:
        """Find the best person-machine combination for a job considering availability"""
        current_op = env.todo_time_step_job[job_idx]
        machine_id = env.instance_matrix[job_idx][current_op][0]
        proc_time = env.instance_matrix[job_idx][current_op][1]
        
        # Get the earliest available person for this machine
        person_id, person_available_time = self._get_earliest_available_person(machine_id, current_time)
        
        # Calculate when the machine will be available
        machine_available_time = env.time_until_available_machine[machine_id]
        machine_ready_time = current_time + machine_available_time
        
        # The job can start when both person and machine are available
        start_time = max(person_available_time, machine_ready_time)
        
        return person_id, start_time, start_time + proc_time

    def _cleanup_expired_assignments(self, current_time: float):
        """Remove expired people assignments"""
        expired_people = []
        for person_id, assignment in self.people_assignments.items():
            if assignment['end_time'] <= current_time:
                expired_people.append(person_id)
        
        for person_id in expired_people:
            del self.people_assignments[person_id]
        
        # Debug info if there are many active assignments
        if len(self.people_assignments) > self.num_people:
            print(f"Warning: More assignments ({len(self.people_assignments)}) than people ({self.num_people})")
            print(f"Active assignments: {[(pid, assn['end_time']) for pid, assn in self.people_assignments.items()]}")

    def _get_resource_utilization(self, current_time: float) -> Dict[str, float]:
        """Calculate current resource utilization metrics"""
        busy_people = 0
        total_wait_time = 0
        
        for person_id, assignment in self.people_assignments.items():
            if assignment['end_time'] > current_time:
                busy_people += 1
            else:
                # Person will be free, calculate when
                wait_time = max(0, assignment['end_time'] - current_time)
                total_wait_time += wait_time
        
        person_utilization = busy_people / self.num_people if self.num_people > 0 else 0.0
        avg_person_wait = total_wait_time / self.num_people if self.num_people > 0 else 0.0
        
        return {
            'person_utilization': person_utilization,
            'avg_person_wait': avg_person_wait,
            'busy_people': busy_people
        }

    def __call__(self, env, obs: Dict[str, np.ndarray]) -> int:
        """Select action considering controller constraints - never skip valid jobs"""
        if isinstance(obs, dict) and "action_mask" in obs:
            legal_actions = obs["action_mask"]
        else:
            legal_actions = env.get_legal_actions()

        # Validate legal_actions size
        expected_action_size = env.jobs + 1  # jobs plus no-op
        if len(legal_actions) != expected_action_size:
            print(
                f"Error: legal_actions size {len(legal_actions)} does not match expected {expected_action_size}")
            return env.jobs

        current_time = env.current_time_step
        
        # Clean up expired assignments
        self._cleanup_expired_assignments(current_time)
        
        # Reset consecutive no-op counter if time has advanced significantly
        if current_time > self.last_action_time + 1.0:
            self.consecutive_no_ops = 0
        self.last_action_time = current_time
        
        # Find all jobs that have remaining operations
        available_jobs = []
        job_info = {}
        
        # Find all legal jobs (even if they have resource constraints)
        all_legal_jobs = []
        
        for i in range(env.jobs):
            # Check legal actions, job completion, and that there are actually more operations
            if (legal_actions[i] and 
                env.todo_time_step_job[i] < env.machines and 
                env.todo_time_step_job[i] < len(env.instance_matrix[i])):
                all_legal_jobs.append(i)
                current_op = env.todo_time_step_job[i]
                machine_id = env.instance_matrix[i][current_op][0]
                
                try:
                    # Find the best person-machine combination for this job
                    person_id, start_time, end_time = self._find_best_person_machine_combination(env, i, current_time)
                    
                    job_info[i] = {
                        'person_id': person_id,
                        'machine_id': machine_id,
                        'start_time': start_time,
                        'end_time': end_time,
                        'current_op': current_op
                    }
                    available_jobs.append(i)
                    
                except ValueError as e:
                    # Handle jobs with no qualified people - this is a critical issue
                    print(f"Critical Warning: {e} for job {i}, machine {machine_id}")
                    print("Controller configuration may be incomplete!")
                    
                    # Check if there are ANY people qualified for this machine
                    qualified_people = [pid for pid, machines in self.controller.items() 
                                      if machine_id in machines]
                    if not qualified_people:
                        print(f"FATAL: No people are qualified for machine {machine_id}")
                        print(f"Available people: {list(self.controller.keys())}")
                        print(f"Machine assignments: {[(pid, machines) for pid, machines in self.controller.items()]}")
                        raise ValueError(f"Controller configuration error: no people qualified for machine {machine_id}")
                    
                    continue

        # CRITICAL: Never skip all jobs - ensure scheduling progress
        if not available_jobs:
            if all_legal_jobs:
                # Before forcing, double-check that jobs are actually not completed and have operations remaining
                truly_incomplete_jobs = [job for job in all_legal_jobs 
                                       if (env.todo_time_step_job[job] < env.machines and 
                                           env.todo_time_step_job[job] < len(env.instance_matrix[job]))]
                if truly_incomplete_jobs:
                    print(f"WARNING: No immediately available jobs, but {len(truly_incomplete_jobs)} incomplete legal jobs exist")
                    print("This suggests controller configuration issues - forcing first incomplete legal job")
                    forced_job = truly_incomplete_jobs[0]
                    return forced_job
                else:
                    # All jobs are actually completed
                    return env.jobs if legal_actions[env.jobs] else 0
            else:
                # Truly no legal actions available
                return env.jobs if legal_actions[env.jobs] else 0

        # Calculate scores for each available job
        job_scores = {}
        for job_idx in available_jobs:
            score = self._calculate_job_score_enhanced(env, job_idx, current_time, job_info[job_idx])
            job_scores[job_idx] = score

        # IMPROVED SCHEDULING LOGIC: Always schedule a job to avoid excessive waiting
        
        # 1. First, try to find jobs that can start immediately
        immediate_jobs = [job for job in available_jobs 
                         if job_info[job]['start_time'] <= current_time + 0.1]
        
        if immediate_jobs:
            # Score immediate jobs and pick the best one
            immediate_scores = {job: job_scores[job] for job in immediate_jobs}
            best_immediate = max(immediate_scores.keys(), key=lambda x: immediate_scores[x])
            
            # Update person assignment
            immediate_info = job_info[best_immediate]
            self.people_assignments[immediate_info['person_id']] = {
                'machine_id': immediate_info['machine_id'],
                'end_time': immediate_info['end_time'],
                'job_id': best_immediate
            }
            self.consecutive_no_ops = 0
            return best_immediate
        
        # 2. If no immediate jobs, check if we've been waiting too long
        if self.consecutive_no_ops >= self.max_consecutive_no_ops:
            # Force scheduling to prevent infinite waiting
            best_job = max(job_scores.keys(), key=lambda x: job_scores[x])
            best_info = job_info[best_job]
            self.people_assignments[best_info['person_id']] = {
                'machine_id': best_info['machine_id'],
                'end_time': best_info['end_time'],
                'job_id': best_job
            }
            self.consecutive_no_ops = 0
            return best_job
        
        # 3. Find the job with minimum waiting time
        min_wait_job = min(available_jobs, key=lambda x: job_info[x]['start_time'])
        min_wait_time = job_info[min_wait_job]['start_time'] - current_time
        
        # 4. If minimum wait time is reasonable, schedule the best job among those with shortest wait
        max_acceptable_wait = max(env.max_time_op * 0.1, 1.0)  # At least 1 time unit or 10% of max op time
        if min_wait_time <= max_acceptable_wait:
            # Find all jobs with similar wait times (within 20% of minimum)
            tolerance = max(1.0, min_wait_time * 0.2)
            short_wait_jobs = [job for job in available_jobs 
                             if job_info[job]['start_time'] - current_time <= min_wait_time + tolerance]
            
            # Select best job among short-wait jobs
            short_wait_scores = {job: job_scores[job] for job in short_wait_jobs}
            best_short_wait = max(short_wait_scores.keys(), key=lambda x: short_wait_scores[x])
            
            # Update person assignment
            best_info = job_info[best_short_wait]
            self.people_assignments[best_info['person_id']] = {
                'machine_id': best_info['machine_id'],
                'end_time': best_info['end_time'],
                'job_id': best_short_wait
            }
            self.consecutive_no_ops = 0
            return best_short_wait
        
        # 5. Check resource utilization - if most people are busy, wait a bit
        resource_util = self._get_resource_utilization(current_time)
        
        # If utilization is high (>80%) and average wait is short, wait briefly
        if (resource_util['person_utilization'] > 0.8 and 
            resource_util['avg_person_wait'] <= max_acceptable_wait * 0.5):
            self.consecutive_no_ops += 1
            return env.jobs if legal_actions[env.jobs] else 0
        
        # 6. Otherwise, schedule the best available job to ensure progress
        best_job = max(job_scores.keys(), key=lambda x: job_scores[x])
        best_info = job_info[best_job]
        self.people_assignments[best_info['person_id']] = {
            'machine_id': best_info['machine_id'],
            'end_time': best_info['end_time'],
            'job_id': best_job
        }
        self.consecutive_no_ops = 0
        return best_job

    def _calculate_job_score(self, env, job_idx: int, current_time: float) -> float:
        """Calculate composite score for a job"""
        current_op = env.todo_time_step_job[job_idx]
        proc_time = env.instance_matrix[job_idx][current_op][1]
        machine_id = env.instance_matrix[job_idx][current_op][0]

        # SPT score (Shortest Processing Time)
        spt_score = 1.0 - \
            (proc_time / env.max_time_op) if env.max_time_op > 0 else 1.0

        # Work remaining score
        remaining_work = sum(env.instance_matrix[job_idx][op][1]
                             for op in range(current_op + 1, env.machines))
        work_remaining_score = remaining_work / \
            (env.max_time_op * env.machines) if env.max_time_op > 0 else 0.0

        # Machine availability score
        machine_available_time = env.time_until_available_machine[machine_id]
        machine_util_score = 1.0 - \
            (machine_available_time / env.max_time_op) if env.max_time_op > 0 else 1.0

        # Person availability score
        available_people = self._get_available_people(machine_id, current_time)
        person_availability_score = len(
            available_people) / self.num_people if self.num_people > 0 else 0.0

        # Critical path score (new)
        earliest_start = max(current_time, machine_available_time)
        critical_path_score = 1.0 - \
            (earliest_start / env.max_time_op) if env.max_time_op > 0 else 1.0

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

    def _calculate_job_score_enhanced(self, env, job_idx: int, current_time: float, job_info: Dict) -> float:
        """Calculate enhanced composite score for a job considering actual availability"""
        current_op = job_info['current_op']
        machine_id = job_info['machine_id']
        start_time = job_info['start_time']
        proc_time = env.instance_matrix[job_idx][current_op][1]

        # SPT score (Shortest Processing Time) - higher score for shorter tasks
        spt_score = 1.0 - (proc_time / env.max_time_op) if env.max_time_op > 0 else 1.0

        # Work remaining score - prioritize jobs with more remaining work
        remaining_work = sum(env.instance_matrix[job_idx][op][1]
                             for op in range(current_op + 1, env.machines))
        max_possible_work = env.max_time_op * env.machines
        work_remaining_score = remaining_work / max_possible_work if max_possible_work > 0 else 0.0

        # Waiting time penalty - prefer jobs that can start sooner
        wait_time = max(0, start_time - current_time)
        max_wait = env.max_time_op if env.max_time_op > 0 else 1.0
        wait_penalty = max(0, 1.0 - (wait_time / max_wait))

        # Machine utilization score - prefer machines that are available sooner
        machine_available_time = env.time_until_available_machine[machine_id]
        machine_util_score = 1.0 - (machine_available_time / env.max_time_op) if env.max_time_op > 0 else 1.0

        # Person availability score - consider how many people can work on this machine
        qualified_people_count = sum(1 for allowed_machines in self.controller.values() 
                                   if machine_id in allowed_machines)
        person_availability_score = qualified_people_count / self.num_people if self.num_people > 0 else 0.0

        # Critical path consideration - jobs with fewer remaining operations get higher priority
        operations_remaining = env.machines - current_op
        critical_path_score = 1.0 - (operations_remaining / env.machines) if env.machines > 0 else 1.0

        # Resource efficiency - prefer combinations that use resources efficiently
        resource_efficiency = 1.0 if wait_time == 0 else max(0.1, 1.0 - (wait_time / max_wait))

        # Dynamic weights based on scheduling progress
        total_ops = env.jobs * env.machines
        completed_ops = sum(env.todo_time_step_job[j] for j in range(env.jobs))
        progress = completed_ops / total_ops if total_ops > 0 else 0.0

        if progress < 0.3:  # Early stage - focus on critical path and work remaining
            weights = {
                'spt': 0.15,
                'work_remaining': 0.25,
                'wait_penalty': 0.20,
                'machine_util': 0.15,
                'person_availability': 0.10,
                'critical_path': 0.10,
                'resource_efficiency': 0.05
            }
        elif progress < 0.7:  # Middle stage - balanced approach
            weights = {
                'spt': 0.20,
                'work_remaining': 0.20,
                'wait_penalty': 0.20,
                'machine_util': 0.15,
                'person_availability': 0.15,
                'critical_path': 0.05,
                'resource_efficiency': 0.05
            }
        else:  # Late stage - focus on completion
            weights = {
                'spt': 0.30,
                'work_remaining': 0.15,
                'wait_penalty': 0.25,
                'machine_util': 0.10,
                'person_availability': 0.10,
                'critical_path': 0.05,
                'resource_efficiency': 0.05
            }

        score = (weights['spt'] * spt_score +
                weights['work_remaining'] * work_remaining_score +
                weights['wait_penalty'] * wait_penalty +
                weights['machine_util'] * machine_util_score +
                weights['person_availability'] * person_availability_score +
                weights['critical_path'] * critical_path_score +
                weights['resource_efficiency'] * resource_efficiency)

        return score

    def run_episode(self) -> Tuple[float, float, List[Tuple[int, int, float, float, int]]]:
        """Run a single episode and collect scheduling information"""
        schedule = []  # Store (job_id, machine_id, start_time, end_time, person_id)
        obs, _ = self.env.reset()
        done = False
        total_reward = 0
        # Track completed operations per job
        completed_ops = {i: set() for i in range(self.env.jobs)}
        # Track current assignments for better schedule recording
        current_action_assignments = {}
        
        # Add safety mechanism to prevent infinite loops
        max_iterations = self.env.jobs * self.env.machines * 10  # Conservative upper bound
        iteration_count = 0

        while not done and iteration_count < max_iterations:
            iteration_count += 1
            action = self.__call__(self.env, obs)

            # Enhanced validation for action
            if action >= self.env.jobs and action != self.env.jobs:
                action = self.env.jobs
            elif action < self.env.jobs:
                # Double-check that the job is not completed
                if self.env.todo_time_step_job[action] >= self.env.machines:
                    action = self.env.jobs
                # Also check if the job has any remaining operations in the instance matrix
                elif self.env.todo_time_step_job[action] >= len(self.env.instance_matrix[action]):
                    action = self.env.jobs
                # Additional safety check for legal actions
                elif not obs["action_mask"][action] if isinstance(obs, dict) and "action_mask" in obs else not self.env.get_legal_actions()[action]:
                    action = self.env.jobs

            # Before taking the step, record the assignment if it's a valid job action
            if action < self.env.jobs:
                current_op = self.env.todo_time_step_job[action]
                if current_op < self.env.machines and current_op < len(self.env.instance_matrix[action]):
                    machine_id = self.env.instance_matrix[action][current_op][0]
                    proc_time = self.env.instance_matrix[action][current_op][1]
                    current_time = self.env.current_time_step
                    
                    # Find the assigned person from our assignments
                    assigned_person = None
                    for person_id, assignment in self.people_assignments.items():
                        if (assignment.get('job_id') == action and 
                            assignment.get('machine_id') == machine_id):
                            assigned_person = person_id
                            break
                    
                    # If no assigned person found, try to get one
                    if assigned_person is None:
                        try:
                            assigned_person, _ = self._get_earliest_available_person(machine_id, current_time)
                        except ValueError:
                            print(f"Warning: Could not find person for job {action}, machine {machine_id}")
                            assigned_person = 0  # Default to person 0
                    
                    if assigned_person is not None:
                        # Calculate actual start and end times
                        machine_available_time = self.env.time_until_available_machine[machine_id]
                        actual_start_time = max(current_time, current_time + machine_available_time)
                        actual_end_time = actual_start_time + proc_time
                        
                        current_action_assignments[action] = {
                            'person_id': assigned_person,
                            'machine_id': machine_id,
                            'start_time': actual_start_time,
                            'end_time': actual_end_time,
                            'current_op': current_op
                        }

            step_result = self.env.step(action)

            if len(step_result) == 5:
                obs, reward, done, truncated, _ = step_result
            else:
                obs, reward, done, _ = step_result
                truncated = False

            total_reward += reward

            # Record scheduling decision for non-no-op actions
            if action < self.env.jobs and action in current_action_assignments:
                assignment = current_action_assignments[action]
                current_op = assignment['current_op']
                
                # Only record if this operation hasn't been recorded before
                if current_op not in completed_ops[action]:
                    schedule.append((
                        action,
                        assignment['machine_id'],
                        assignment['start_time'],
                        assignment['end_time'],
                        assignment['person_id']
                    ))
                    completed_ops[action].add(current_op)
                    
                # Clean up the assignment record
                del current_action_assignments[action]
            elif action < self.env.jobs:
                # If we took a job action but didn't record it properly, try to recover
                current_op = self.env.todo_time_step_job[action] - 1  # Operation that was just completed
                if current_op >= 0 and current_op not in completed_ops[action]:
                    print(f"DEBUG: Recovering missing record for job {action}, operation {current_op}")
                    # Create a basic schedule entry
                    machine_id = self.env.instance_matrix[action][current_op][0]
                    proc_time = self.env.instance_matrix[action][current_op][1]
                    current_time = self.env.current_time_step
                    
                    schedule.append((
                        action,
                        machine_id,
                        current_time - proc_time,  # Estimate start time
                        current_time,  # End time is current time
                        0  # Default person
                    ))
                    completed_ops[action].add(current_op)

            if truncated:
                done = True
        
        if iteration_count >= max_iterations:
            print(f"Warning: Episode terminated due to maximum iterations ({max_iterations}) reached")

        makespan = self.env.current_time_step
        print(f"Schedule contains {len(schedule)} tasks")
        
        # Enhanced verification of scheduled operations
        actual_total_ops = 0
        for job_id in range(self.env.jobs):
            job_ops = len(self.env.instance_matrix[job_id])
            completed_for_job = len(completed_ops[job_id])
            actual_total_ops += job_ops
            if completed_for_job < job_ops:
                print(f"Job {job_id}: scheduled {completed_for_job}/{job_ops} operations")
                missing_ops = set(range(job_ops)) - completed_ops[job_id]
                print(f"  Missing operations: {sorted(missing_ops)}")
        
        # print(f"Total operations in instance: {actual_total_ops}")
        # print(f"Operations scheduled: {len(schedule)}")
        
        if len(schedule) < actual_total_ops:
            print(f"Warning: Expected {actual_total_ops} operations, but only scheduled {len(schedule)}")
            
            # Additional debugging: check final job states
            print("\nFinal job states:")
            for job_id in range(self.env.jobs):
                current_op = self.env.todo_time_step_job[job_id]
                total_ops = len(self.env.instance_matrix[job_id])
                print(f"  Job {job_id}: operation {current_op}/{total_ops}")
        
        return makespan, total_reward, schedule

    def get_name(self) -> str:
        """Return agent name for compatibility with comparison framework"""
        return self.name
