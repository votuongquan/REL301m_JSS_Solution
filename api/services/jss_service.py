"""
JSS Service - Business logic layer
"""

import asyncio
import time
import uuid
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from project modules
import sys
import gym
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent.parent))

from api.schemas.jss_schemas import (
	AgentType,
	BackgroundTaskStatus,
	ComparisonRequest,
	ComparisonResult,
	ControllerInfo,
	ControllerStats,
	InstanceInfo,
	InstanceStats,
	PerformanceMetrics,
	SingleRunRequest,
	SingleRunResult,
	VisualizationRequest,
)
from comparison_framework.agents import (
	AdaptiveLookAheadAgent,
	BaseJSSAgent,
	HybridPriorityScoringAgent,
)
from comparison_framework.advanced_visualizer import AdvancedJSSVisualizer
from comparison_framework.comparison_framework import JSSComparisonFramework
from controller_agent import ControllerJSSAgent


class JSSFileService:
	"""Service for handling JSS files (instances and controllers)"""

	def __init__(self, instances_dir: str, controllers_dir: str, results_dir: str = None):
		self.instances_dir = Path(instances_dir)
		self.controllers_dir = Path(controllers_dir)
		self.results_dir = Path(results_dir) if results_dir else Path('results')

		# Ensure directories exist
		self.instances_dir.mkdir(exist_ok=True)
		self.controllers_dir.mkdir(exist_ok=True)
		self.results_dir.mkdir(exist_ok=True)

	def get_instances(self, include_stats: bool = False) -> List[InstanceInfo]:
		"""Get list of available instances with optional detailed stats"""
		instances = []
		if self.instances_dir.exists():
			for file_path in self.instances_dir.iterdir():
				if file_path.is_file():
					instance_info = self._parse_instance_file(file_path, include_stats)
					instances.append(instance_info)
		return sorted(instances, key=lambda x: x.name)

	def get_controllers(self, include_stats: bool = False) -> List[ControllerInfo]:
		"""Get list of available controllers with optional detailed stats"""
		controllers = []
		if self.controllers_dir.exists():
			for file_path in self.controllers_dir.iterdir():
				if file_path.is_file() and file_path.suffix == '.txt':
					controller_info = self._parse_controller_file(file_path, include_stats)
					controllers.append(controller_info)
		return sorted(controllers, key=lambda x: x.name)

	def _parse_instance_file(self, file_path: Path, include_stats: bool = False) -> InstanceInfo:
		"""Parse instance file and extract information"""
		# Basic info
		size = 'Unknown'
		stats = None
		created_at = None
		file_size = None

		try:
			file_stat = file_path.stat()
			created_at = datetime.fromtimestamp(file_stat.st_ctime, tz=timezone.utc)
			file_size = file_stat.st_size

			with open(file_path, 'r') as f:
				lines = f.readlines()
				if lines:
					first_line = lines[0].strip()
					parts = first_line.split()
					if len(parts) >= 2:
						num_jobs = int(parts[0])
						num_machines = int(parts[1])
						size = f'{num_jobs}x{num_machines}'

						if include_stats:
							# Calculate detailed stats
							total_operations = 0
							processing_times = []

							# Parse job lines
							for i in range(1, min(num_jobs + 1, len(lines))):
								job_line = lines[i].strip().split()
								operations = len(job_line) // 2
								total_operations += operations

								# Extract processing times
								for j in range(1, len(job_line), 2):
									if j < len(job_line):
										processing_times.append(int(job_line[j]))

							avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
							complexity_score = (num_jobs * num_machines * total_operations) / 1000.0  # Normalized complexity

							stats = InstanceStats(
								name=file_path.name,
								num_jobs=num_jobs,
								num_machines=num_machines,
								total_operations=total_operations,
								avg_processing_time=avg_processing_time,
								complexity_score=complexity_score,
							)
		except Exception as e:
			print(f'Warning: Could not parse instance file {file_path}: {e}')

		return InstanceInfo(
			name=file_path.name,
			path=str(file_path),
			size=size,
			stats=stats,
			created_at=created_at,
			file_size=file_size,
		)

	def _parse_controller_file(self, file_path: Path, include_stats: bool = False) -> ControllerInfo:
		"""Parse controller file and extract information"""
		num_people = 0
		num_machines = 0
		stats = None
		created_at = None
		file_size = None

		try:
			file_stat = file_path.stat()
			created_at = datetime.fromtimestamp(file_stat.st_ctime, tz=timezone.utc)
			file_size = file_stat.st_size

			with open(file_path, 'r') as f:
				lines = f.readlines()
				num_people = len([line for line in lines if line.strip()])

				machines = set()
				qualifications_per_person = []

				for line in lines:
					if line.strip():
						person_machines = list(map(int, line.strip().split()))
						machines.update(person_machines)
						qualifications_per_person.append(len(person_machines))

				num_machines = len(machines)

				if include_stats and qualifications_per_person:
					avg_qualifications = sum(qualifications_per_person) / len(qualifications_per_person)
					max_possible_machines = max(machines) if machines else 1
					coverage_percentage = (num_machines / max_possible_machines) * 100 if max_possible_machines > 0 else 0

					stats = ControllerStats(
						name=file_path.stem,
						num_people=num_people,
						num_machines=num_machines,
						avg_qualifications_per_person=avg_qualifications,
						coverage_percentage=coverage_percentage,
					)
		except Exception as e:
			print(f'Warning: Could not parse controller file {file_path}: {e}')

		return ControllerInfo(
			name=file_path.stem,
			path=str(file_path),
			num_people=num_people,
			num_machines=num_machines,
			stats=stats,
			created_at=created_at,
			file_size=file_size,
		)

	def get_instance_path(self, instance_name: str) -> str:
		"""Get full path for instance"""
		return str(self.instances_dir / instance_name)

	def get_controller_path(self, controller_name: str) -> str:
		"""Get full path for controller"""
		return str(self.controllers_dir / f'{controller_name}.txt')

	def instance_exists(self, instance_name: str) -> bool:
		"""Check if instance exists"""
		return (self.instances_dir / instance_name).exists()

	def controller_exists(self, controller_name: str) -> bool:
		"""Check if controller exists"""
		return (self.controllers_dir / f'{controller_name}.txt').exists()


class JSSExecutionService:
	"""Service for executing JSS algorithms"""

	def __init__(self, file_service: JSSFileService):
		self.file_service = file_service
		self.executor = ThreadPoolExecutor(max_workers=4)
		self.background_tasks: Dict[str, BackgroundTaskStatus] = {}
		# Do not instantiate AdvancedJSSVisualizer here; instantiate with results when needed

	# Background Task Management
	def create_background_task(self, task_type: str) -> str:
		"""Create a new background task and return its ID"""
		task_id = str(uuid.uuid4())
		self.background_tasks[task_id] = BackgroundTaskStatus(
			task_id=task_id,
			status='pending',
			created_at=datetime.now(timezone.utc),
			updated_at=datetime.now(timezone.utc),
		)
		return task_id

	def get_task_status(self, task_id: str) -> Optional[BackgroundTaskStatus]:
		"""Get status of a background task"""
		return self.background_tasks.get(task_id)

	def get_all_tasks(self) -> List[BackgroundTaskStatus]:
		"""Get all background tasks"""
		return list(self.background_tasks.values())

	def update_task_status(
		self,
		task_id: str,
		status: str,
		progress: float = None,
		result: Any = None,
		error: str = None,
	):
		"""Update background task status"""
		if task_id in self.background_tasks:
			task = self.background_tasks[task_id]
			task.status = status
			task.updated_at = datetime.now(timezone.utc)
			if progress is not None:
				task.progress = progress
			if result is not None:
				task.result = result
			if error is not None:
				task.error = error

	# Synchronous execution methods

	# Background execution methods
	async def run_comparison_background(self, request: ComparisonRequest) -> str:
		"""Run comparison in background and return task ID"""
		task_id = self.create_background_task('comparison')

		# Start background task
		asyncio.create_task(self._run_comparison_background_task(task_id, request))

		return task_id

	async def _run_comparison_background_task(self, task_id: str, request: ComparisonRequest):
		"""Background task for running comparison"""
		try:
			self.update_task_status(task_id, 'running', 0.0)

			# Validate inputs
			instance_path = self.file_service.get_instance_path(request.instance_name)
			if not self.file_service.instance_exists(request.instance_name):
				raise ValueError(f"Instance '{request.instance_name}' not found")

			controller_path = None
			if request.controller_name:
				if not self.file_service.controller_exists(request.controller_name):
					raise ValueError(f"Controller '{request.controller_name}' not found")
				controller_path = self.file_service.get_controller_path(request.controller_name)

			self.update_task_status(task_id, 'running', 20.0)

			# Run comparison
			loop = asyncio.get_event_loop()
			result = await loop.run_in_executor(
				self.executor,
				self._run_comparison_sync,
				request,
				instance_path,
				controller_path,
			)

			self.update_task_status(task_id, 'running', 80.0)

			# Generate visualizations if requested
			if request.include_visualizations:
				await self._generate_visualizations_for_result(result, task_id)

			self.update_task_status(task_id, 'completed', 100.0, result.dict())

		except Exception as e:
			self.update_task_status(task_id, 'failed', error=str(e))

	# Visualization methods
	async def generate_visualizations(self, request: VisualizationRequest) -> Dict[str, str]:
		"""Generate visualizations for comparison results"""
		results_dir = self.file_service.results_dir
		visualization_paths = {}

		# Create results directory for this request
		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
		results_subdir = results_dir / f'{request.instance_name}_{timestamp}'
		results_subdir.mkdir(exist_ok=True)

		try:
			# Generate requested visualizations
			if 'dashboard' in request.visualization_types:
				dashboard_path = results_subdir / f'dashboard.{request.format}'
				# Use visualizer to generate dashboard
				await self._generate_dashboard(request, dashboard_path, None)
				visualization_paths['dashboard'] = str(dashboard_path)

			if 'detailed' in request.visualization_types:
				detailed_path = results_subdir / f'detailed_comparison.{request.format}'
				await self._generate_detailed_comparison(request, detailed_path, None)
				visualization_paths['detailed'] = str(detailed_path)

			if 'gantt' in request.visualization_types:
				gantt_dir = results_subdir / 'gantt_charts'
				gantt_dir.mkdir(exist_ok=True)
				gantt_paths = await self._generate_gantt_charts(request, gantt_dir, request.format, None)
				visualization_paths.update(gantt_paths)

		except Exception as e:
			raise ValueError(f'Failed to generate visualizations: {str(e)}')

		return visualization_paths

	async def _generate_visualizations_for_result(self, result: ComparisonResult, task_id: str):
		"""Generate visualizations for a comparison result"""
		try:
			# Create results directory for this task
			timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
			results_subdir = self.file_service.results_dir / f'{result.instance_name}_{timestamp}'
			results_subdir.mkdir(exist_ok=True)

			# Convert ComparisonResult to dict for AdvancedJSSVisualizer
			visualizer_results = {}
			for method_name, metrics in result.results.items():
				# If metrics is a pydantic model, convert to dict
				if hasattr(metrics, 'dict'):
					metrics = metrics.dict()
				visualizer_results[method_name] = metrics

			visualizer = AdvancedJSSVisualizer(visualizer_results, result.instance_name)
			dashboard_path = results_subdir / 'comprehensive_dashboard.png'
			visualizer.create_comprehensive_dashboard(str(dashboard_path))
			detailed_path = results_subdir / 'detailed_comparison.png'
			visualizer.create_detailed_comparison(str(detailed_path))
			print(f'📊 Visualizations generated in {results_subdir}')
		except Exception as e:
			print(f'Warning: Failed to generate visualizations for task {task_id}: {e}')

	async def _generate_dashboard(
		self,
		request: VisualizationRequest,
		output_path: Path,
		results_data: Dict = None,
	):
		"""Generate comprehensive dashboard"""
		if results_data:
			visualizer = AdvancedJSSVisualizer(results_data, request.instance_name)
			visualizer.create_comprehensive_dashboard(str(output_path))
		else:
			# Create placeholder when no results data available
			print(f'Warning: No results data available for dashboard generation')

	async def _generate_detailed_comparison(
		self,
		request: VisualizationRequest,
		output_path: Path,
		results_data: Dict = None,
	):
		"""Generate detailed comparison chart"""
		if results_data:
			visualizer = AdvancedJSSVisualizer(results_data, request.instance_name)
			visualizer.create_detailed_comparison(str(output_path))
		else:
			print(f'Warning: No results data available for detailed comparison generation')

	async def _generate_gantt_charts(
		self,
		request: VisualizationRequest,
		output_dir: Path,
		format: str,
		results_data: Dict = None,
	) -> Dict[str, str]:
		"""Generate Gantt charts for different agents"""
		if results_data:
			# Generate Gantt charts would require additional schedule data
			# This is a placeholder for now - would need to be implemented with actual schedule data
			print(f'Gantt chart generation not yet implemented')
		return {}

	# File management methods
	def list_result_files(self, pattern: str = None) -> List[Dict[str, Any]]:
		"""List result files in the results directory"""
		files = []
		results_dir = self.file_service.results_dir

		if results_dir.exists():
			for item in results_dir.rglob('*'):
				if item.is_file():
					if pattern is None or pattern in item.name:
						file_info = {
							'name': item.name,
							'path': str(item.relative_to(results_dir)),
							'full_path': str(item),
							'size': item.stat().st_size,
							'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
							'type': item.suffix.lower().lstrip('.'),
						}
						files.append(file_info)

		return sorted(files, key=lambda x: x['modified'], reverse=True)

	def get_file_path(self, relative_path: str) -> str:
		"""Get full path for a result file"""
		full_path = self.file_service.results_dir / relative_path
		if full_path.exists() and full_path.is_file():
			return str(full_path)
		raise FileNotFoundError(f'File not found: {relative_path}')

	def _create_agent(
		self,
		agent_type: AgentType,
		instance_path: str = None,
		controller_path: str = None,
		num_people: int = None,
	) -> BaseJSSAgent:
		"""Create agent instance based on type"""
		if agent_type == AgentType.HYBRID:
			return HybridPriorityScoringAgent()
		elif agent_type == AgentType.LOOKAHEAD:
			return AdaptiveLookAheadAgent()
		elif agent_type == AgentType.CONTROLLER:
			if not all([instance_path, controller_path, num_people]):
				raise ValueError('Controller agent requires instance_path, controller_path, and num_people')
			return ControllerJSSAgent(instance_path, controller_path, num_people)
		else:
			raise ValueError(f'Unknown agent type: {agent_type}')

	def _run_comparison_sync(
		self,
		request: ComparisonRequest,
		instance_path: str,
		controller_path: Optional[str],
	) -> ComparisonResult:
		"""Synchronous comparison execution"""
		start_time = time.time()

		# Initialize framework
		framework = JSSComparisonFramework(instance_path)

		# Create custom agents
		custom_agents = []
		for agent_type in request.agents:
			if agent_type == AgentType.CONTROLLER and controller_path:
				# Get controller info for num_people
				controller_info = next(
					(c for c in self.file_service.get_controllers() if c.name == request.controller_name),
					None,
				)
				if controller_info:
					agent = self._create_agent(
						agent_type,
						instance_path,
						controller_path,
						controller_info.num_people,
					)
					custom_agents.append(agent)
			else:
				agent = self._create_agent(agent_type)
				custom_agents.append(agent)

		# Run comparison
		results_df = framework.run_comprehensive_comparison(custom_agents=custom_agents, num_episodes=request.num_episodes)

		# Convert results to response format
		results_dict = {}
		for method, metrics in framework.results.items():
			results_dict[method] = PerformanceMetrics(
				avg_makespan=metrics['avg_makespan'],
				std_makespan=metrics['std_makespan'],
				min_makespan=metrics['min_makespan'],
				max_makespan=metrics['max_makespan'],
				avg_reward=metrics['avg_reward'],
				std_reward=metrics['std_reward'],
				avg_execution_time=metrics['avg_execution_time'],
				total_episodes=metrics['total_episodes'],
			)

		# Get best method
		best_method = results_df.iloc[0]['Method']
		best_makespan = results_df.iloc[0]['Avg_Makespan']
		ranking = results_df['Method'].tolist()

		execution_time = time.time() - start_time

		return ComparisonResult(
			instance_name=request.instance_name,
			controller_name=request.controller_name,
			results=results_dict,
			best_method=best_method,
			best_makespan=best_makespan,
			ranking=ranking,
			execution_summary={
				'total_execution_time': execution_time,
				'episodes_per_method': request.num_episodes,
				'methods_compared': len(results_dict),
				'custom_agents': len(custom_agents),
				'dispatching_rules': len(request.dispatching_rules),
			},
		)

	async def run_single_episode(self, request: SingleRunRequest) -> SingleRunResult:
		"""Run a single episode with specified agent"""
		instance_path = self.file_service.get_instance_path(request.instance_name)

		if not self.file_service.instance_exists(request.instance_name):
			raise ValueError(f"Instance '{request.instance_name}' not found")

		controller_path = None
		num_people = None
		if request.controller_name:
			if not self.file_service.controller_exists(request.controller_name):
				raise ValueError(f"Controller '{request.controller_name}' not found")
			controller_path = self.file_service.get_controller_path(request.controller_name)

			# Get controller info
			controller_info = next(
				(c for c in self.file_service.get_controllers() if c.name == request.controller_name),
				None,
			)
			if controller_info:
				num_people = controller_info.num_people
			elif request.num_people:
				num_people = request.num_people

		# Run single episode in thread pool
		loop = asyncio.get_event_loop()
		result = await loop.run_in_executor(
			self.executor,
			self._run_single_episode_sync,
			request,
			instance_path,
			controller_path,
			num_people,
		)

		return result

	def _run_single_episode_sync(
		self,
		request: SingleRunRequest,
		instance_path: str,
		controller_path: Optional[str],
		num_people: Optional[int],
	) -> SingleRunResult:
		"""Synchronous single episode execution"""
		start_time = time.time()

		# Create agent
		if request.agent_type == AgentType.CONTROLLER:
			if not all([controller_path, num_people]):
				raise ValueError('Controller agent requires controller and num_people')
			agent = ControllerJSSAgent(instance_path, controller_path, num_people)
			makespan, total_reward, schedule = agent.run_episode()

			# Convert schedule format
			schedule_tasks = []
			for task in schedule:
				schedule_tasks.append({
					'job_id': task[0],
					'machine_id': task[1],
					'start_time': task[2],
					'end_time': task[3],
					'person_id': task[4] if len(task) > 4 else None,
				})
		else:
			# Use comparison framework for other agents
			framework = JSSComparisonFramework(instance_path)
			agent = self._create_agent(request.agent_type)

			# Run single episode with schedule capture
			makespan, total_reward, execution_time, schedule = framework.env_manager.run_episode_with_schedule_capture(lambda env, obs: agent(env, obs))

			# Convert schedule format
			schedule_tasks = []
			for task in schedule:
				schedule_tasks.append({
					'job_id': task[0],
					'machine_id': task[1],
					'start_time': task[2],
					'end_time': task[3],
					'person_id': None,
				})

		execution_time = time.time() - start_time

		return SingleRunResult(
			instance_name=request.instance_name,
			controller_name=request.controller_name,
			agent_type=request.agent_type.value,
			makespan=makespan,
			total_reward=total_reward,
			execution_time=execution_time,
			schedule=schedule_tasks,
		)

	def _run_comparison_sync(
		self,
		request: ComparisonRequest,
		instance_path: str,
		controller_path: Optional[str],
	) -> ComparisonResult:
		"""Synchronous comparison execution"""
		start_time = time.time()

		# Initialize framework
		framework = JSSComparisonFramework(instance_path)

		# Create custom agents
		custom_agents = []
		for agent_type in request.agents:
			if agent_type == AgentType.CONTROLLER and controller_path:
				# Get controller info for num_people
				controller_info = next(
					(c for c in self.file_service.get_controllers() if c.name == request.controller_name),
					None,
				)
				if controller_info:
					agent = self._create_agent(
						agent_type,
						instance_path,
						controller_path,
						controller_info.num_people,
					)
					custom_agents.append(agent)
			else:
				agent = self._create_agent(agent_type)
				custom_agents.append(agent)

		# Run comparison
		results_df = framework.run_comprehensive_comparison(custom_agents=custom_agents, num_episodes=request.num_episodes)

		# Convert results to response format
		results_dict = {}
		for method, metrics in framework.results.items():
			results_dict[method] = PerformanceMetrics(
				avg_makespan=metrics['avg_makespan'],
				std_makespan=metrics['std_makespan'],
				min_makespan=metrics['min_makespan'],
				max_makespan=metrics['max_makespan'],
				avg_reward=metrics['avg_reward'],
				std_reward=metrics['std_reward'],
				avg_execution_time=metrics['avg_execution_time'],
				total_episodes=metrics['total_episodes'],
			)

		# Get best method
		best_method = results_df.iloc[0]['Method']
		best_makespan = results_df.iloc[0]['Avg_Makespan']
		ranking = results_df['Method'].tolist()

		execution_time = time.time() - start_time

		return ComparisonResult(
			instance_name=request.instance_name,
			controller_name=request.controller_name,
			results=results_dict,
			best_method=best_method,
			best_makespan=best_makespan,
			ranking=ranking,
			execution_summary={
				'total_execution_time': execution_time,
				'episodes_per_method': request.num_episodes,
				'methods_compared': len(results_dict),
				'custom_agents': len(custom_agents),
				'dispatching_rules': len(request.dispatching_rules),
			},
		)
