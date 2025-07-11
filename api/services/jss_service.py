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


# ANSI color codes for beautiful logging
class Colors:
	RED = '\033[91m'
	GREEN = '\033[92m'
	YELLOW = '\033[93m'
	BLUE = '\033[94m'
	MAGENTA = '\033[95m'
	CYAN = '\033[96m'
	WHITE = '\033[97m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'
	END = '\033[0m'


def log(message: str, color: str = Colors.WHITE, prefix: str = 'INFO'):
	"""Enhanced logging with colors"""
	timestamp = datetime.now().strftime('%H:%M:%S')
	print(f'{Colors.BOLD}[{timestamp}]{Colors.END} {color}{prefix}:{Colors.END} {message}')


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
		log(f'🚀 Initializing JSSFileService', Colors.CYAN, 'INIT')
		self.instances_dir = Path(instances_dir)
		self.controllers_dir = Path(controllers_dir)
		self.results_dir = Path(results_dir) if results_dir else Path('results')

		# Ensure directories exist
		log(f'📁 Creating directories if needed...', Colors.BLUE, 'SETUP')
		self.instances_dir.mkdir(exist_ok=True)
		self.controllers_dir.mkdir(exist_ok=True)
		self.results_dir.mkdir(exist_ok=True)
		log(
			f'✅ Directories ready: instances={self.instances_dir}, controllers={self.controllers_dir}, results={self.results_dir}',
			Colors.GREEN,
			'SETUP',
		)

	def get_instances(self, include_stats: bool = False) -> List[InstanceInfo]:
		"""Get list of available instances with optional detailed stats"""
		log(
			f'📋 Getting instances list (include_stats={include_stats})',
			Colors.BLUE,
			'FETCH',
		)
		instances = []
		if self.instances_dir.exists():
			for file_path in self.instances_dir.iterdir():
				if file_path.is_file():
					log(
						f'  📄 Processing instance: {file_path.name}',
						Colors.YELLOW,
						'PARSE',
					)
					instance_info = self._parse_instance_file(file_path, include_stats)
					instances.append(instance_info)
		log(f'✅ Found {len(instances)} instances', Colors.GREEN, 'FETCH')
		return sorted(instances, key=lambda x: x.name)

	def get_controllers(self, include_stats: bool = False) -> List[ControllerInfo]:
		"""Get list of available controllers with optional detailed stats"""
		log(
			f'🎮 Getting controllers list (include_stats={include_stats})',
			Colors.BLUE,
			'FETCH',
		)
		controllers = []
		if self.controllers_dir.exists():
			for file_path in self.controllers_dir.iterdir():
				if file_path.is_file() and file_path.suffix == '.txt':
					log(
						f'  📄 Processing controller: {file_path.name}',
						Colors.YELLOW,
						'PARSE',
					)
					controller_info = self._parse_controller_file(file_path, include_stats)
					controllers.append(controller_info)
		log(f'✅ Found {len(controllers)} controllers', Colors.GREEN, 'FETCH')
		return sorted(controllers, key=lambda x: x.name)

	def _parse_instance_file(self, file_path: Path, include_stats: bool = False) -> InstanceInfo:
		"""Parse instance file and extract information"""
		log(f'🔍 Parsing instance file: {file_path.name}', Colors.CYAN, 'PARSE')
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
						log(
							f'  📊 Instance size: {size} (jobs={num_jobs}, machines={num_machines})',
							Colors.MAGENTA,
							'PARSE',
						)

						if include_stats:
							log(
								f'  🔬 Calculating detailed statistics...',
								Colors.YELLOW,
								'STATS',
							)
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
							log(
								f'  ✅ Stats calculated: ops={total_operations}, avg_time={avg_processing_time:.2f}, complexity={complexity_score:.2f}',
								Colors.GREEN,
								'STATS',
							)
		except Exception as e:
			log(
				f'❌ Warning: Could not parse instance file {file_path}: {e}',
				Colors.RED,
				'ERROR',
			)

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
		log(f'🎮 Parsing controller file: {file_path.name}', Colors.CYAN, 'PARSE')
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
				log(
					f'  👥 Controller info: {num_people} people, {num_machines} machines',
					Colors.MAGENTA,
					'PARSE',
				)

				if include_stats and qualifications_per_person:
					log(
						f'  🔬 Calculating controller statistics...',
						Colors.YELLOW,
						'STATS',
					)
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
					log(
						f'  ✅ Stats calculated: avg_quals={avg_qualifications:.2f}, coverage={coverage_percentage:.2f}%',
						Colors.GREEN,
						'STATS',
					)
		except Exception as e:
			log(
				f'❌ Warning: Could not parse controller file {file_path}: {e}',
				Colors.RED,
				'ERROR',
			)

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
		# Log initialization details
		print(f'DEBUG: Initializing JSSExecutionService with file service: {file_service}')
		log(f'⚡ Initializing JSSExecutionService', Colors.CYAN, 'INIT')
		self.file_service = file_service
		self.executor = ThreadPoolExecutor(max_workers=4)
		self.background_tasks: Dict[str, BackgroundTaskStatus] = {}
		log(
			f'✅ JSSExecutionService ready with {self.executor._max_workers} worker threads',
			Colors.GREEN,
			'INIT',
		)
		# Do not instantiate AdvancedJSSVisualizer here; instantiate with results when needed

	# Background Task Management
	def create_background_task(self, task_type: str) -> str:
		"""Create a new background task and return its ID"""
		task_id = str(uuid.uuid4())
		log(
			f'🚀 Creating background task: {task_id[:8]}... (type: {task_type})',
			Colors.BLUE,
			'TASK',
		)
		self.background_tasks[task_id] = BackgroundTaskStatus(
			task_id=task_id,
			status='pending',
			created_at=datetime.now(timezone.utc),
			updated_at=datetime.now(timezone.utc),
		)
		return task_id

	def get_task_status(self, task_id: str) -> Optional[BackgroundTaskStatus]:
		"""Get status of a background task"""
		log(f'📊 Getting task status: {task_id[:8]}...', Colors.BLUE, 'TASK')
		task = self.background_tasks.get(task_id)
		if task:
			log(
				f'  ✅ Task found: status={task.status}, progress={task.progress}',
				Colors.GREEN,
				'TASK',
			)
		else:
			log(f'  ❌ Task not found', Colors.RED, 'TASK')
		return task

	def get_all_tasks(self) -> List[BackgroundTaskStatus]:
		"""Get all background tasks"""
		log(f'📋 Getting all background tasks', Colors.BLUE, 'TASK')
		tasks = list(self.background_tasks.values())
		log(f'  ✅ Found {len(tasks)} tasks', Colors.GREEN, 'TASK')
		return tasks

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
			old_status = task.status
			task.status = status
			task.updated_at = datetime.now(timezone.utc)

			color = Colors.BLUE
			if status == 'completed':
				color = Colors.GREEN
			elif status == 'failed':
				color = Colors.RED
			elif status == 'running':
				color = Colors.YELLOW

			log(
				f'🔄 Task {task_id[:8]}... status: {old_status} → {status}',
				color,
				'TASK',
			)

			if progress is not None:
				task.progress = progress
				log(f'  📊 Progress: {progress:.1f}%', Colors.CYAN, 'TASK')
			if result is not None:
				task.result = result
				log(f'  ✅ Result stored', Colors.GREEN, 'TASK')
			if error is not None:
				task.error = error
				log(f'  ❌ Error: {error}', Colors.RED, 'TASK')

	# Synchronous execution methods
	async def run_comparison(self, request: ComparisonRequest) -> ComparisonResult:
		"""Run comparison synchronously"""
		log(
			f'🚀 Starting synchronous comparison for instance: {request.instance_name}',
			Colors.MAGENTA,
			'COMP',
		)
		log(f'  📋 Agents: {[a.value for a in request.agents]}', Colors.CYAN, 'COMP')
		log(f'  🔢 Episodes: {request.num_episodes}', Colors.CYAN, 'COMP')

		# Validate inputs
		instance_path = self.file_service.get_instance_path(request.instance_name)
		if not self.file_service.instance_exists(request.instance_name):
			log(f'❌ Instance not found: {request.instance_name}', Colors.RED, 'ERROR')
			raise ValueError(f"Instance '{request.instance_name}' not found")

		controller_path = None
		if request.controller_name:
			if not self.file_service.controller_exists(request.controller_name):
				log(
					f'❌ Controller not found: {request.controller_name}',
					Colors.RED,
					'ERROR',
				)
				raise ValueError(f"Controller '{request.controller_name}' not found")
			controller_path = self.file_service.get_controller_path(request.controller_name)
			log(
				f'  🎮 Using controller: {request.controller_name}',
				Colors.YELLOW,
				'COMP',
			)

		# Run comparison in thread pool to avoid blocking
		log(f'⚡ Running comparison in thread pool...', Colors.BLUE, 'COMP')
		loop = asyncio.get_event_loop()
		result = await loop.run_in_executor(
			self.executor,
			self._run_comparison_sync,
			request,
			instance_path,
			controller_path,
		)

		log(
			f'✅ Comparison completed! Best method: {result.best_method} (makespan: {result.best_makespan})',
			Colors.GREEN,
			'COMP',
		)
		return result

	# Background execution methods
	async def run_comparison_background(self, request: ComparisonRequest) -> str:
		"""Run comparison in background and return task ID"""
		log(
			f'🚀 Starting background comparison for instance: {request.instance_name}',
			Colors.MAGENTA,
			'BG',
		)
		print(f'DEBUG: Starting background comparison with request: {request.dict()}')
		task_id = self.create_background_task('comparison')

		# Start background task
		log(f'  ⚡ Creating background task: {task_id[:8]}...', Colors.BLUE, 'BG')
		asyncio.create_task(self._run_comparison_background_task(task_id, request))

		return task_id

	async def _run_comparison_background_task(self, task_id: str, request: ComparisonRequest):
		"""Background task for running comparison"""
		try:
			log(f'🏃 Background task {task_id[:8]}... starting', Colors.YELLOW, 'BG')
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
			log(f'⚡ Task {task_id[:8]}... running comparison', Colors.BLUE, 'BG')
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
				log(
					f'🎨 Task {task_id[:8]}... generating visualizations',
					Colors.CYAN,
					'BG',
				)
				await self._generate_visualizations_for_result(result, task_id)

			log(f'✅ Task {task_id[:8]}... completed successfully!', Colors.GREEN, 'BG')
			self.update_task_status(task_id, 'completed', 100.0, result.dict())

		except Exception as e:
			log(f'❌ Task {task_id[:8]}... failed: {str(e)}', Colors.RED, 'BG')
			self.update_task_status(task_id, 'failed', error=str(e))

	# Visualization methods
	async def generate_visualizations(self, request: VisualizationRequest) -> Dict[str, str]:
		"""Generate visualizations for comparison results"""
		log(
			f'🎨 Generating visualizations for {request.instance_name}',
			Colors.MAGENTA,
			'VIZ',
		)
		log(f'  📊 Types: {request.visualization_types}', Colors.CYAN, 'VIZ')

		results_dir = self.file_service.results_dir
		visualization_paths = {}

		# Create results directory for this request
		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
		results_subdir = results_dir / f'{request.instance_name}_{timestamp}'
		results_subdir.mkdir(exist_ok=True)
		log(f'  📁 Created results directory: {results_subdir}', Colors.BLUE, 'VIZ')

		try:
			# Generate requested visualizations
			if 'dashboard' in request.visualization_types:
				log(f'  🏠 Generating dashboard...', Colors.YELLOW, 'VIZ')
				dashboard_path = results_subdir / f'dashboard.{request.format}'
				await self._generate_dashboard(request, dashboard_path, None)
				visualization_paths['dashboard'] = str(dashboard_path)

			if 'detailed' in request.visualization_types:
				log(f'  📈 Generating detailed comparison...', Colors.YELLOW, 'VIZ')
				detailed_path = results_subdir / f'detailed_comparison.{request.format}'
				await self._generate_detailed_comparison(request, detailed_path, None)
				visualization_paths['detailed'] = str(detailed_path)

			if 'gantt' in request.visualization_types:
				log(f'  📊 Generating Gantt charts...', Colors.YELLOW, 'VIZ')
				gantt_dir = results_subdir / 'gantt_charts'
				gantt_dir.mkdir(exist_ok=True)
				gantt_paths = await self._generate_gantt_charts(request, gantt_dir, request.format, None)
				visualization_paths.update(gantt_paths)

			log(
				f'✅ Generated {len(visualization_paths)} visualizations',
				Colors.GREEN,
				'VIZ',
			)
		except Exception as e:
			log(f'❌ Visualization generation failed: {str(e)}', Colors.RED, 'VIZ')
			raise ValueError(f'Failed to generate visualizations: {str(e)}')

		return visualization_paths

	async def _generate_visualizations_for_result(self, result: ComparisonResult, task_id: str):
		"""Generate visualizations for a comparison result"""
		try:
			log(
				f'🎨 Generating visualizations for task {task_id[:8]}...',
				Colors.MAGENTA,
				'VIZ',
			)
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

			log(f'  📊 Creating comprehensive dashboard...', Colors.YELLOW, 'VIZ')
			visualizer = AdvancedJSSVisualizer(visualizer_results, result.instance_name)
			dashboard_path = results_subdir / 'comprehensive_dashboard.png'
			visualizer.create_comprehensive_dashboard(str(dashboard_path))

			log(f'  📈 Creating detailed comparison...', Colors.YELLOW, 'VIZ')
			detailed_path = results_subdir / 'detailed_comparison.png'
			visualizer.create_detailed_comparison(str(detailed_path))

			log(f'📊 Visualizations generated in {results_subdir}', Colors.GREEN, 'VIZ')
		except Exception as e:
			log(
				f'❌ Warning: Failed to generate visualizations for task {task_id}: {e}',
				Colors.RED,
				'VIZ',
			)

	async def _generate_dashboard(
		self,
		request: VisualizationRequest,
		output_path: Path,
		results_data: Dict = None,
	):
		"""Generate comprehensive dashboard"""
		if results_data:
			log(
				f'  🏠 Creating dashboard with data at {output_path}',
				Colors.BLUE,
				'VIZ',
			)
			visualizer = AdvancedJSSVisualizer(results_data, request.instance_name)
			visualizer.create_comprehensive_dashboard(str(output_path))
			log(f'  ✅ Dashboard created successfully', Colors.GREEN, 'VIZ')
		else:
			# Create placeholder when no results data available
			log(
				f'⚠️ Warning: No results data available for dashboard generation',
				Colors.YELLOW,
				'VIZ',
			)

	async def _generate_detailed_comparison(
		self,
		request: VisualizationRequest,
		output_path: Path,
		results_data: Dict = None,
	):
		"""Generate detailed comparison chart"""
		if results_data:
			log(
				f'  📈 Creating detailed comparison at {output_path}',
				Colors.BLUE,
				'VIZ',
			)
			visualizer = AdvancedJSSVisualizer(results_data, request.instance_name)
			visualizer.create_detailed_comparison(str(output_path))
			log(f'  ✅ Detailed comparison created successfully', Colors.GREEN, 'VIZ')
		else:
			log(
				f'⚠️ Warning: No results data available for detailed comparison generation',
				Colors.YELLOW,
				'VIZ',
			)

	async def _generate_gantt_charts(
		self,
		request: VisualizationRequest,
		output_dir: Path,
		format: str,
		results_data: Dict = None,
	) -> Dict[str, str]:
		"""Generate Gantt charts for different agents"""
		if results_data:
			log(f'  📊 Creating Gantt charts in {output_dir}', Colors.BLUE, 'VIZ')
			# Generate Gantt charts would require additional schedule data
			# This is a placeholder for now - would need to be implemented with actual schedule data
			log(f'⚠️ Gantt chart generation not yet implemented', Colors.YELLOW, 'VIZ')
		else:
			log(
				f'⚠️ Warning: No results data available for Gantt chart generation',
				Colors.YELLOW,
				'VIZ',
			)
		return {}

	# File management methods
	def list_result_files(self, pattern: str = None) -> List[Dict[str, Any]]:
		"""List result files in the results directory"""
		log(f'📂 Listing result files (pattern: {pattern})', Colors.BLUE, 'FILES')
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

		log(f'✅ Found {len(files)} files', Colors.GREEN, 'FILES')
		return sorted(files, key=lambda x: x['modified'], reverse=True)

	def get_file_path(self, relative_path: str) -> str:
		"""Get full path for a result file"""
		log(f'📁 Getting file path: {relative_path}', Colors.BLUE, 'FILES')
		full_path = self.file_service.results_dir / relative_path
		if full_path.exists() and full_path.is_file():
			log(f'✅ File found: {full_path}', Colors.GREEN, 'FILES')
			return str(full_path)
		log(f'❌ File not found: {relative_path}', Colors.RED, 'FILES')
		raise FileNotFoundError(f'File not found: {relative_path}')

	def _create_agent(
		self,
		agent_type: AgentType,
		instance_path: str = None,
		controller_path: str = None,
		num_people: int = None,
	) -> BaseJSSAgent:
		"""Create agent instance based on type"""
		log(f'🤖 Creating agent: {agent_type.value}', Colors.MAGENTA, 'AGENT')

		if agent_type == AgentType.HYBRID:
			agent = HybridPriorityScoringAgent()
			log(f'  ✅ HybridPriorityScoringAgent created', Colors.GREEN, 'AGENT')
			return agent
		elif agent_type == AgentType.LOOKAHEAD:
			agent = AdaptiveLookAheadAgent()
			log(f'  ✅ AdaptiveLookAheadAgent created', Colors.GREEN, 'AGENT')
			return agent
		elif agent_type == AgentType.CONTROLLER:
			if not all([instance_path, controller_path, num_people]):
				log(
					f'❌ Controller agent requires instance_path, controller_path, and num_people',
					Colors.RED,
					'AGENT',
				)
				raise ValueError('Controller agent requires instance_path, controller_path, and num_people')
			agent = ControllerJSSAgent(instance_path, controller_path, num_people)
			log(
				f'  ✅ ControllerJSSAgent created with {num_people} people',
				Colors.GREEN,
				'AGENT',
			)
			return agent
		else:
			log(f'❌ Unknown agent type: {agent_type}', Colors.RED, 'AGENT')
			raise ValueError(f'Unknown agent type: {agent_type}')

	def _run_comparison_sync(
		self,
		request: ComparisonRequest,
		instance_path: str,
		controller_path: Optional[str],
	) -> ComparisonResult:
		"""Synchronous comparison execution"""
		log(f'⚡ Running synchronous comparison', Colors.BLUE, 'COMP')
		start_time = time.time()

		# Initialize framework
		log(f'  🏗️ Initializing JSS framework with {instance_path}', Colors.CYAN, 'COMP')
		framework = JSSComparisonFramework(instance_path)

		# Create custom agents
		custom_agents = []
		log(f'  🤖 Creating {len(request.agents)} agents...', Colors.YELLOW, 'COMP')
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
		log(
			f'  🏃 Running comprehensive comparison with {request.num_episodes} episodes...',
			Colors.BLUE,
			'COMP',
		)
		results_df = framework.run_comprehensive_comparison(custom_agents=custom_agents, num_episodes=request.num_episodes)

		# Convert results to response format
		log(f'  📊 Converting results to response format...', Colors.CYAN, 'COMP')
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
		log(f'  ✅ Comparison completed in {execution_time:.2f}s', Colors.GREEN, 'COMP')
		log(
			f'  🏆 Best method: {best_method} (makespan: {best_makespan})',
			Colors.MAGENTA,
			'COMP',
		)

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
		log(
			f'🎯 Running single episode for {request.instance_name} with {request.agent_type.value}',
			Colors.MAGENTA,
			'EPISODE',
		)

		instance_path = self.file_service.get_instance_path(request.instance_name)

		if not self.file_service.instance_exists(request.instance_name):
			log(f'❌ Instance not found: {request.instance_name}', Colors.RED, 'EPISODE')
			raise ValueError(f"Instance '{request.instance_name}' not found")

		controller_path = None
		num_people = None
		if request.controller_name:
			if not self.file_service.controller_exists(request.controller_name):
				log(
					f'❌ Controller not found: {request.controller_name}',
					Colors.RED,
					'EPISODE',
				)
				raise ValueError(f"Controller '{request.controller_name}' not found")
			controller_path = self.file_service.get_controller_path(request.controller_name)
			log(
				f'  🎮 Using controller: {request.controller_name}',
				Colors.YELLOW,
				'EPISODE',
			)

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
		log(f'⚡ Running episode in thread pool...', Colors.BLUE, 'EPISODE')
		loop = asyncio.get_event_loop()
		result = await loop.run_in_executor(
			self.executor,
			self._run_single_episode_sync,
			request,
			instance_path,
			controller_path,
			num_people,
		)

		log(
			f'✅ Episode completed! Makespan: {result.makespan}, Reward: {result.total_reward}',
			Colors.GREEN,
			'EPISODE',
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
		log(f'⚡ Running single episode synchronously', Colors.BLUE, 'EPISODE')
		start_time = time.time()

		# Create agent
		if request.agent_type == AgentType.CONTROLLER:
			if not all([controller_path, num_people]):
				log(
					f'❌ Controller agent requires controller and num_people',
					Colors.RED,
					'EPISODE',
				)
				raise ValueError('Controller agent requires controller and num_people')

			log(
				f'  🎮 Creating controller agent with {num_people} people',
				Colors.YELLOW,
				'EPISODE',
			)
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
			log(
				f'  🤖 Creating {request.agent_type.value} agent',
				Colors.YELLOW,
				'EPISODE',
			)
			framework = JSSComparisonFramework(instance_path)
			agent = self._create_agent(request.agent_type)

			# Run single episode with schedule capture
			log(f'  🏃 Running episode with schedule capture...', Colors.CYAN, 'EPISODE')
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
		log(f'  ✅ Episode completed in {execution_time:.2f}s', Colors.GREEN, 'EPISODE')
		log(
			f'  📊 Results: makespan={makespan}, reward={total_reward}, tasks={len(schedule_tasks)}',
			Colors.MAGENTA,
			'EPISODE',
		)

		return SingleRunResult(
			instance_name=request.instance_name,
			controller_name=request.controller_name,
			agent_type=request.agent_type.value,
			makespan=makespan,
			total_reward=total_reward,
			execution_time=execution_time,
			schedule=schedule_tasks,
		)
