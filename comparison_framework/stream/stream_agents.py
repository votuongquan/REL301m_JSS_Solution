"""
Lightweight JSS Agents for Streaming Implementation
Optimized for real-time performance without visualization dependencies
"""

import numpy as np
import time
from typing import Dict, List, Callable

# Import JSS environment
try:
    from JSSEnv.envs.jss_env import JssEnv
    import gym
except ImportError:
    # Handle case where JSSEnv is not installed
    pass


class BaseStreamJSSAgent:
    """Base class for streaming JSS agents - lightweight version"""

    def __init__(self, name: str):
        self.name = name

    def __call__(self, env, obs: Dict[str, np.ndarray]) -> int:
        """Select action based on environment state and observation"""
        raise NotImplementedError

    def get_name(self) -> str:
        return self.name

    def reset(self):
        """Reset agent state for new episode"""
        pass


class StreamHybridPriorityScoringAgent(BaseStreamJSSAgent):
    """
    Streamlined version of HybridPriorityScoringAgent for real-time streaming
    Focuses on performance and minimal overhead
    """

    def __init__(self):
        super().__init__('HybridPriorityScoring')
        self.episode_step = 0
        self.total_jobs = 0
        self.total_machines = 0
        
    def reset(self):
        """Reset agent state for new episode"""
        self.episode_step = 0
        self.total_jobs = 0
        self.total_machines = 0

    def __call__(self, env, obs: Dict[str, np.ndarray]) -> int:
        # Handle observation format
        if isinstance(obs, dict) and 'action_mask' in obs:
            legal_actions = obs['action_mask']
        else:
            legal_actions = obs

        # If only no-op is legal, return it
        if np.sum(legal_actions[:-1]) == 0 and legal_actions[-1]:
            return env.jobs

        # Initialize problem parameters at start
        if self.episode_step == 0:
            self.total_jobs = env.jobs
            self.total_machines = env.machines

        self.episode_step += 1

        # Calculate progress ratio
        progress_ratio = self._calculate_progress_ratio(env)

        # Get legal job indices
        legal_job_indices = [i for i in range(env.jobs) if legal_actions[i]]

        if not legal_job_indices:
            return env.jobs  # No-op

        # Calculate composite scores for each legal job
        job_scores = {}
        for job_idx in legal_job_indices:
            job_scores[job_idx] = self._calculate_job_score(env, job_idx, progress_ratio)

        # Select best job (highest score)
        best_job = max(job_scores.keys(), key=lambda x: job_scores[x])

        # Occasionally consider no-op if it's legal and we're early in schedule
        if legal_actions[env.jobs] and progress_ratio < 0.3 and np.random.random() < 0.05:
            return env.jobs

        return best_job

    def _calculate_progress_ratio(self, env) -> float:
        """Calculate how far we are through the scheduling process"""
        completed_ops = sum(env.todo_time_step_job)
        total_ops = env.jobs * env.machines
        return completed_ops / total_ops if total_ops > 0 else 0.0

    def _calculate_job_score(self, env, job_idx: int, progress_ratio: float) -> float:
        """Calculate composite priority score for a job"""
        
        # Get job information
        current_op = env.todo_time_step_job[job_idx]
        current_machine = env.needed_machine_jobs[job_idx]
        current_proc_time = env.instance_matrix[job_idx][current_op][1]

        # Calculate various heuristic components
        spt_score = self._shortest_processing_time_score(current_proc_time, env.max_time_op)
        work_remaining_score = self._work_remaining_score(env, job_idx)
        critical_path_score = self._critical_path_score(env, job_idx)
        machine_utilization_score = self._machine_utilization_score(env, current_machine)
        bottleneck_score = self._bottleneck_machine_score(env, job_idx, current_op)
        flow_continuity_score = self._flow_continuity_score(env, job_idx, current_op)

        # Dynamic weight adjustment based on progress
        weights = self._get_dynamic_weights(progress_ratio, env)

        # Composite score
        composite_score = (
            weights['spt'] * spt_score +
            weights['work_remaining'] * work_remaining_score +
            weights['critical_path'] * critical_path_score +
            weights['machine_util'] * machine_utilization_score +
            weights['bottleneck'] * bottleneck_score +
            weights['flow_continuity'] * flow_continuity_score
        )

        return composite_score

    def _shortest_processing_time_score(self, proc_time: int, max_time: int) -> float:
        """SPT heuristic - favor shorter processing times"""
        return 1.0 - (proc_time / max_time) if max_time > 0 else 0.5

    def _work_remaining_score(self, env, job_idx: int) -> float:
        """Calculate remaining work for this job"""
        current_op = env.todo_time_step_job[job_idx]
        remaining_work = sum(
            env.instance_matrix[job_idx][op][1] 
            for op in range(current_op, env.machines)
        )
        max_remaining = env.max_time_jobs
        return remaining_work / max_remaining if max_remaining > 0 else 0.5

    def _critical_path_score(self, env, job_idx: int) -> float:
        """Estimate critical path importance"""
        current_op = env.todo_time_step_job[job_idx]
        remaining_ops = env.machines - current_op
        return remaining_ops / env.machines if env.machines > 0 else 0.5

    def _machine_utilization_score(self, env, machine_id: int) -> float:
        """Score based on machine utilization"""
        # Simple approximation based on machine workload
        machine_load = sum(1 for job in range(env.jobs) 
                          if env.needed_machine_jobs[job] == machine_id 
                          and env.todo_time_step_job[job] < env.machines)
        return 1.0 - (machine_load / env.jobs) if env.jobs > 0 else 0.5

    def _bottleneck_machine_score(self, env, job_idx: int, current_op: int) -> float:
        """Score based on bottleneck analysis"""
        current_machine = env.needed_machine_jobs[job_idx]
        current_proc_time = env.instance_matrix[job_idx][current_op][1]
        
        # Simple bottleneck detection
        total_machine_load = sum(
            env.instance_matrix[j][op][1] 
            for j in range(env.jobs) 
            for op in range(env.machines)
            if env.instance_matrix[j][op][0] == current_machine
        )
        
        avg_machine_load = total_machine_load / env.jobs if env.jobs > 0 else 1
        return current_proc_time / avg_machine_load if avg_machine_load > 0 else 0.5

    def _flow_continuity_score(self, env, job_idx: int, current_op: int) -> float:
        """Score based on maintaining job flow"""
        if current_op == 0:
            return 1.0  # First operation always has good flow
        
        prev_machine = env.instance_matrix[job_idx][current_op - 1][0]
        current_machine = env.instance_matrix[job_idx][current_op][0]
        
        # Prefer continuing on different machines to avoid blocking
        return 0.8 if prev_machine != current_machine else 0.4

    def _get_dynamic_weights(self, progress_ratio: float, env) -> Dict[str, float]:
        """Get dynamic weights based on scheduling progress"""
        
        # Early stage: focus on SPT and work remaining
        if progress_ratio < 0.3:
            return {
                'spt': 0.4,
                'work_remaining': 0.3,
                'critical_path': 0.1,
                'machine_util': 0.1,
                'bottleneck': 0.05,
                'flow_continuity': 0.05
            }
        
        # Middle stage: balanced approach
        elif progress_ratio < 0.7:
            return {
                'spt': 0.25,
                'work_remaining': 0.25,
                'critical_path': 0.2,
                'machine_util': 0.15,
                'bottleneck': 0.1,
                'flow_continuity': 0.05
            }
        
        # Late stage: focus on critical path and bottlenecks
        else:
            return {
                'spt': 0.15,
                'work_remaining': 0.15,
                'critical_path': 0.3,
                'machine_util': 0.2,
                'bottleneck': 0.15,
                'flow_continuity': 0.05
            }


class StreamAdaptiveLookAheadAgent(BaseStreamJSSAgent):
    """
    Streamlined lookahead agent for real-time streaming
    """

    def __init__(self, lookahead_depth: int = 2):
        super().__init__('AdaptiveLookAhead')
        self.lookahead_depth = lookahead_depth
        
    def reset(self):
        """Reset agent state for new episode"""
        pass

    def __call__(self, env, obs: Dict[str, np.ndarray]) -> int:
        # Handle observation format
        if isinstance(obs, dict) and 'action_mask' in obs:
            legal_actions = obs['action_mask']
        else:
            legal_actions = obs

        # Get legal actions
        legal_job_indices = [i for i in range(env.jobs) if legal_actions[i]]
        
        if not legal_job_indices:
            return env.jobs  # No-op
        
        if len(legal_job_indices) == 1:
            return legal_job_indices[0]

        # Simple lookahead evaluation
        best_action = legal_job_indices[0]
        best_score = float('-inf')

        for action in legal_job_indices:
            score = self._evaluate_action_with_lookahead(env, action)
            if score > best_score:
                best_score = score
                best_action = action

        return best_action

    def _evaluate_action_with_lookahead(self, env, action: int) -> float:
        """
        Simplified lookahead evaluation for streaming performance
        """
        try:
            # Save current state
            current_state = env._get_state() if hasattr(env, '_get_state') else None
            
            # Take action and evaluate immediate reward
            _, reward, done, _ = env.step(action)
            immediate_reward = reward
            
            # If we can lookahead further and not done
            if self.lookahead_depth > 1 and not done:
                # Simple heuristic: estimate future reward
                future_reward = self._estimate_future_reward(env)
                total_score = immediate_reward + 0.9 * future_reward
            else:
                total_score = immediate_reward
            
            # Restore state if possible
            if current_state is not None and hasattr(env, '_set_state'):
                env._set_state(current_state)
            
            return total_score
            
        except Exception:
            # Fallback to simple heuristic if environment doesn't support state save/restore
            return self._simple_action_heuristic(env, action)

    def _estimate_future_reward(self, env) -> float:
        """Estimate future reward using simple heuristics"""
        # Simple estimation based on remaining work
        total_remaining = sum(
            sum(env.instance_matrix[job][op][1] 
                for op in range(env.todo_time_step_job[job], env.machines))
            for job in range(env.jobs)
        )
        
        # Normalize to a reasonable range
        avg_remaining = total_remaining / (env.jobs * env.machines) if env.jobs * env.machines > 0 else 0
        return -avg_remaining  # Negative because less remaining work is better

    def _simple_action_heuristic(self, env, action: int) -> float:
        """Simple heuristic when lookahead is not possible"""
        if action >= env.jobs:  # No-op action
            return -0.1
        
        current_op = env.todo_time_step_job[action]
        proc_time = env.instance_matrix[action][current_op][1]
        
        # Prefer shorter processing times
        return -proc_time / env.max_time_op if env.max_time_op > 0 else 0


class StreamControllerJSSAgent(BaseStreamJSSAgent):
    """
    Streamlined controller agent for real-time streaming
    """

    def __init__(self, controller_path: str, num_people: int = None):
        super().__init__('ControllerAgent')
        self.controller_path = controller_path
        self.num_people = num_people
        self.controller_data = None
        self._load_controller()
        
    def reset(self):
        """Reset agent state for new episode"""
        pass

    def _load_controller(self):
        """Load controller configuration"""
        try:
            with open(self.controller_path, 'r') as f:
                lines = f.readlines()
            
            if lines:
                first_line = lines[0].strip().split()
                if len(first_line) >= 2:
                    total_people = int(first_line[0])
                    total_machines = int(first_line[1])
                    
                    # Use specified number of people or default to all
                    people_to_use = self.num_people if self.num_people else total_people
                    
                    self.controller_data = {
                        'total_people': total_people,
                        'total_machines': total_machines,
                        'people_to_use': people_to_use,
                        'qualifications': []
                    }
                    
                    # Load qualifications for the specified number of people
                    for i in range(1, min(people_to_use + 1, len(lines))):
                        line = lines[i].strip()
                        if line:
                            machines = [int(x) - 1 for x in line.split()]  # Convert to 0-indexed
                            self.controller_data['qualifications'].append(machines)
                            
        except Exception as e:
            print(f"Warning: Could not load controller from {self.controller_path}: {e}")
            self.controller_data = None

    def __call__(self, env, obs: Dict[str, np.ndarray]) -> int:
        # Handle observation format
        if isinstance(obs, dict) and 'action_mask' in obs:
            legal_actions = obs['action_mask']
        else:
            legal_actions = obs

        # Get legal job indices
        legal_job_indices = [i for i in range(env.jobs) if legal_actions[i]]

        if not legal_job_indices:
            return env.jobs  # No-op

        # If no controller data, fall back to simple heuristic
        if not self.controller_data:
            return self._fallback_selection(env, legal_job_indices)

        # Controller-based selection
        return self._controller_selection(env, legal_job_indices)

    def _controller_selection(self, env, legal_job_indices: List[int]) -> int:
        """Select job based on controller qualifications"""
        
        job_scores = {}
        
        for job_idx in legal_job_indices:
            current_op = env.todo_time_step_job[job_idx]
            required_machine = env.needed_machine_jobs[job_idx]
            
            # Count qualified people for this machine
            qualified_people = sum(
                1 for person_machines in self.controller_data['qualifications']
                if required_machine in person_machines
            )
            
            # Score based on availability and processing time
            proc_time = env.instance_matrix[job_idx][current_op][1]
            availability_score = qualified_people / max(1, self.controller_data['people_to_use'])
            time_score = 1.0 - (proc_time / env.max_time_op) if env.max_time_op > 0 else 0.5
            
            # Combine scores (favor jobs with more qualified people and shorter times)
            job_scores[job_idx] = 0.7 * availability_score + 0.3 * time_score

        # Return job with highest score
        return max(job_scores.keys(), key=lambda x: job_scores[x])

    def _fallback_selection(self, env, legal_job_indices: List[int]) -> int:
        """Fallback to SPT when controller data is unavailable"""
        
        best_job = legal_job_indices[0]
        best_time = float('inf')
        
        for job_idx in legal_job_indices:
            current_op = env.todo_time_step_job[job_idx]
            proc_time = env.instance_matrix[job_idx][current_op][1]
            
            if proc_time < best_time:
                best_time = proc_time
                best_job = job_idx
        
        return best_job


# Factory function to create streaming agents
def create_stream_agent(agent_type: str = 'hybrid', **kwargs) -> BaseStreamJSSAgent:
    """Create a streaming agent of the specified type"""
    if agent_type.lower() == 'hybrid':
        return StreamHybridPriorityScoringAgent()
    elif agent_type.lower() == 'lookahead':
        lookahead_depth = kwargs.get('lookahead_depth', 2)
        return StreamAdaptiveLookAheadAgent(lookahead_depth)
    elif agent_type.lower() == 'controller':
        controller_path = kwargs.get('controller_path')
        num_people = kwargs.get('num_people')
        if not controller_path:
            raise ValueError("controller_path is required for controller agent")
        return StreamControllerJSSAgent(controller_path, num_people)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


# Dispatching rule wrapper for streaming
class StreamDispatchingRuleAgent(BaseStreamJSSAgent):
    """Wrapper for dispatching rules in streaming context"""
    
    def __init__(self, rule_name: str):
        super().__init__(f'Rule_{rule_name}')
        self.rule_name = rule_name
        self.rule_function = None
        self._load_rule()
    
    def _load_rule(self):
        """Load the dispatching rule function"""
        try:
            from JSSEnv.dispatching import get_rule
            self.rule_function = get_rule(self.rule_name)
        except ImportError:
            print(f"Warning: Could not load dispatching rule {self.rule_name}")
    
    def reset(self):
        """Reset agent state for new episode"""
        pass
    
    def __call__(self, env, obs: Dict[str, np.ndarray]) -> int:
        if self.rule_function:
            return self.rule_function(env)
        else:
            # Fallback to random legal action
            if isinstance(obs, dict) and 'action_mask' in obs:
                legal_actions = obs['action_mask']
            else:
                legal_actions = obs
            
            legal_indices = [i for i in range(len(legal_actions)) if legal_actions[i]]
            return np.random.choice(legal_indices) if legal_indices else 0


def create_dispatching_rule_agent(rule_name: str) -> StreamDispatchingRuleAgent:
    """Create a dispatching rule agent for streaming"""
    return StreamDispatchingRuleAgent(rule_name)
