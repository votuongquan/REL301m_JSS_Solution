"""
Custom JSS Agents Implementation
"""

from typing import Dict

import numpy as np
from JSSEnv.envs.jss_env import JssEnv


class BaseJSSAgent:
	"""Base class for JSS agents"""

	def __init__(self, name: str):
		self.name = name

	def __call__(self, env: JssEnv, obs: Dict[str, np.ndarray]) -> int:
		"""Select action based on environment state and observation"""
		raise NotImplementedError

	def get_name(self) -> str:
		return self.name


class HybridPriorityScoringAgent(BaseJSSAgent):
	"""
	Advanced JSS agent that combines multiple heuristics with dynamic weighting
	based on problem characteristics and current state.
	"""

	def __init__(self):
		super().__init__('HybridPriorityScoring')
		self.episode_step = 0
		self.total_jobs = 0
		self.total_machines = 0

	def __call__(self, env: JssEnv, obs: Dict[str, np.ndarray]) -> int:
		# Handle observation format
		if isinstance(obs, dict) and 'action_mask' in obs:
			legal_actions = obs['action_mask']
		else:
			legal_actions = env.get_legal_actions()

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
			return env.jobs if legal_actions[env.jobs] else 0

		# Calculate composite scores for each legal job
		job_scores = {}
		for job_idx in legal_job_indices:
			score = self._calculate_job_score(env, job_idx, progress_ratio)
			job_scores[job_idx] = score

		# Select best job (highest score)
		best_job = max(job_scores.keys(), key=lambda x: job_scores[x])

		# Occasionally consider no-op if it's legal and we're early in schedule
		if legal_actions[env.jobs] and progress_ratio < 0.3 and np.random.random() < 0.05:
			return env.jobs

		return best_job

	def _calculate_progress_ratio(self, env: JssEnv) -> float:
		"""Calculate how far we are through the scheduling process"""
		completed_ops = sum(env.todo_time_step_job)
		total_ops = env.jobs * env.machines
		return completed_ops / total_ops if total_ops > 0 else 0.0

	def _calculate_job_score(self, env: JssEnv, job_idx: int, progress_ratio: float) -> float:
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
		composite_score = weights['spt'] * spt_score + weights['work_remaining'] * work_remaining_score + weights['critical_path'] * critical_path_score + weights['machine_util'] * machine_utilization_score + weights['bottleneck'] * bottleneck_score + weights['flow_continuity'] * flow_continuity_score

		return composite_score

	def _shortest_processing_time_score(self, proc_time: int, max_time: int) -> float:
		"""Higher score for shorter processing times"""
		return 1.0 - (proc_time / max_time)

	def _work_remaining_score(self, env: JssEnv, job_idx: int) -> float:
		"""Score based on remaining work - prioritize jobs with more work early, less work late"""
		remaining_work = 0
		for op in range(env.todo_time_step_job[job_idx], env.machines):
			remaining_work += env.instance_matrix[job_idx][op][1]

		max_possible_work = env.max_time_op * env.machines
		normalized_remaining = remaining_work / max_possible_work

		return normalized_remaining  # More work = higher score

	def _critical_path_score(self, env: JssEnv, job_idx: int) -> float:
		"""Score based on critical path considerations"""
		remaining_ops = env.machines - env.todo_time_step_job[job_idx]
		max_remaining_ops = env.machines

		# Jobs with more operations remaining are more critical early on
		return remaining_ops / max_remaining_ops

	def _machine_utilization_score(self, env: JssEnv, machine_id: int) -> float:
		"""Score based on machine availability and utilization"""
		machine_available_time = env.time_until_available_machine[machine_id]

		# Prefer machines that are available sooner
		if env.max_time_op > 0:
			return 1.0 - (machine_available_time / env.max_time_op)
		return 1.0

	def _bottleneck_machine_score(self, env: JssEnv, job_idx: int, current_op: int) -> float:
		"""Identify and prioritize jobs that will use bottleneck machines"""
		current_machine = env.instance_matrix[job_idx][current_op][0]

		# Count how many legal jobs need this machine
		machine_demand = sum(1 for j in range(env.jobs) if env.legal_actions[j] and env.needed_machine_jobs[j] == current_machine)

		# Higher demand = higher bottleneck score
		return machine_demand / env.jobs

	def _flow_continuity_score(self, env: JssEnv, job_idx: int, current_op: int) -> float:
		"""Score based on flow continuity - can the job continue to next operation smoothly?"""
		if current_op >= env.machines - 1:  # Last operation
			return 1.0

		# Check next operation machine availability
		next_machine = env.instance_matrix[job_idx][current_op + 1][0]
		next_machine_available_time = env.time_until_available_machine[next_machine]
		current_proc_time = env.instance_matrix[job_idx][current_op][1]

		# If next machine will be available when current op finishes, higher score
		if next_machine_available_time <= current_proc_time:
			return 1.0
		else:
			# Penalize based on waiting time
			wait_time = next_machine_available_time - current_proc_time
			return max(0.0, 1.0 - (wait_time / env.max_time_op))

	def _get_dynamic_weights(self, progress_ratio: float, env: JssEnv) -> Dict[str, float]:
		"""Adjust heuristic weights based on scheduling progress and problem characteristics"""

		# Early stage (0-30%): Focus on critical path and work remaining
		if progress_ratio < 0.3:
			return {
				'spt': 0.15,
				'work_remaining': 0.25,
				'critical_path': 0.25,
				'machine_util': 0.15,
				'bottleneck': 0.10,
				'flow_continuity': 0.10,
			}

		# Middle stage (30-70%): Balance all factors
		elif progress_ratio < 0.7:
			return {
				'spt': 0.20,
				'work_remaining': 0.20,
				'critical_path': 0.15,
				'machine_util': 0.20,
				'bottleneck': 0.15,
				'flow_continuity': 0.10,
			}

		# Late stage (70-100%): Focus on SPT and machine utilization
		else:
			return {
				'spt': 0.30,
				'work_remaining': 0.10,
				'critical_path': 0.15,
				'machine_util': 0.25,
				'bottleneck': 0.10,
				'flow_continuity': 0.10,
			}


class AdaptiveLookAheadAgent(BaseJSSAgent):
	"""
	Agent that performs limited lookahead to evaluate scheduling decisions
	"""

	def __init__(self, lookahead_depth: int = 2):
		super().__init__('AdaptiveLookAhead')
		self.lookahead_depth = lookahead_depth

	def __call__(self, env: JssEnv, obs: Dict[str, np.ndarray]) -> int:
		if isinstance(obs, dict) and 'action_mask' in obs:
			legal_actions = obs['action_mask']
		else:
			legal_actions = env.get_legal_actions()

		legal_job_indices = [i for i in range(env.jobs) if legal_actions[i]]

		if not legal_job_indices:
			return env.jobs if legal_actions[env.jobs] else 0

		if len(legal_job_indices) == 1:
			return legal_job_indices[0]

		# Evaluate each legal action with lookahead
		best_action = legal_job_indices[0]
		best_score = float('-inf')

		for action in legal_job_indices:
			score = self._evaluate_action_with_lookahead(env, action)
			if score > best_score:
				best_score = score
				best_action = action

		return best_action

	def _evaluate_action_with_lookahead(self, env: JssEnv, action: int) -> float:
		"""Evaluate an action by looking ahead a few steps"""
		# This is a simplified lookahead - in practice, you'd want to simulate
		# the environment state after taking the action

		current_op = env.todo_time_step_job[action]
		proc_time = env.instance_matrix[action][current_op][1]
		machine_needed = env.needed_machine_jobs[action]

		# Calculate immediate benefits
		immediate_score = 0.0

		# Reward shorter processing times
		immediate_score += (env.max_time_op - proc_time) / env.max_time_op

		# Reward using available machines
		if env.time_until_available_machine[machine_needed] == 0:
			immediate_score += 0.5

		# Look ahead to next operation if not last
		future_score = 0.0
		if current_op < env.machines - 1:
			next_machine = env.instance_matrix[action][current_op + 1][0]
			next_proc_time = env.instance_matrix[action][current_op + 1][1]

			# Reward if next machine will be available
			next_available_time = env.time_until_available_machine[next_machine]
			if next_available_time <= proc_time:
				future_score += 0.3

			# Reward shorter next processing time
			future_score += (env.max_time_op - next_proc_time) / (2 * env.max_time_op)

		return immediate_score + future_score


# Factory function to create agents
def create_agent(agent_type: str = 'hybrid') -> BaseJSSAgent:
	"""Create an agent of the specified type"""
	if agent_type.lower() == 'hybrid':
		return HybridPriorityScoringAgent()
	elif agent_type.lower() == 'lookahead':
		return AdaptiveLookAheadAgent()
	else:
		return HybridPriorityScoringAgent()
