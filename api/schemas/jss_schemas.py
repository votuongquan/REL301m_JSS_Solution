from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentType(str, Enum):
	"""Available agent types"""

	HYBRID = 'hybrid'
	LOOKAHEAD = 'lookahead'
	CONTROLLER = 'controller'


class DispatchingRule(str, Enum):
	"""Available dispatching rules"""

	SPT = 'SPT'
	FIFO = 'FIFO'
	MWR = 'MWR'
	LWR = 'LWR'
	MOR = 'MOR'
	LOR = 'LOR'
	CR = 'CR'


class InstanceStats(BaseModel):
	"""Statistics about an instance"""

	name: str = Field(..., description='Instance name')
	num_jobs: int = Field(..., description='Number of jobs')
	num_machines: int = Field(..., description='Number of machines')
	total_operations: int = Field(..., description='Total number of operations')
	avg_processing_time: Optional[float] = Field(None, description='Average processing time')
	complexity_score: Optional[float] = Field(None, description='Complexity score')


class ControllerStats(BaseModel):
	"""Statistics about a controller"""

	name: str = Field(..., description='Controller name')
	num_people: int = Field(..., description='Number of people')
	num_machines: int = Field(..., description='Number of machines covered')
	avg_qualifications_per_person: float = Field(..., description='Average qualifications per person')
	coverage_percentage: float = Field(..., description='Percentage of machines covered')


class InstanceInfo(BaseModel):
	"""Information about a JSS instance"""

	name: str = Field(..., description='Instance name')
	path: str = Field(..., description='File path to instance')
	size: str = Field(..., description='Instance size description')
	stats: Optional[InstanceStats] = Field(None, description='Detailed instance statistics')
	created_at: Optional[datetime] = Field(None, description='File creation time')
	file_size: Optional[int] = Field(None, description='File size in bytes')


class ControllerInfo(BaseModel):
	"""Information about a controller"""

	name: str = Field(..., description='Controller name')
	path: str = Field(..., description='File path to controller')
	num_people: int = Field(..., description='Number of people')
	num_machines: int = Field(..., description='Number of machines')
	stats: Optional[ControllerStats] = Field(None, description='Detailed controller statistics')
	created_at: Optional[datetime] = Field(None, description='File creation time')
	file_size: Optional[int] = Field(None, description='File size in bytes')


class ComparisonRequest(BaseModel):
	"""Request for running JSS comparison"""

	instance_name: str = Field(..., description='Name of the JSS instance')
	controller_name: Optional[str] = Field(None, description='Controller name (optional)')
	agents: List[AgentType] = Field(default=[AgentType.HYBRID], description='Agents to compare')
	dispatching_rules: List[DispatchingRule] = Field(default=[], description='Dispatching rules to compare')
	num_episodes: int = Field(default=10, ge=1, le=100, description='Number of episodes to run')
	include_random_baseline: bool = Field(default=True, description='Include random baseline')
	include_visualizations: bool = Field(default=True, description='Generate visualizations')


class SingleRunRequest(BaseModel):
	"""Request for running a single JSS episode"""

	instance_name: str = Field(..., description='Name of the JSS instance')
	controller_name: Optional[str] = Field(None, description='Controller name (optional)')
	agent_type: AgentType = Field(default=AgentType.HYBRID, description='Agent type to use')
	num_people: Optional[int] = Field(None, description='Number of people (for controller agent)')


class PerformanceMetrics(BaseModel):
	"""Performance metrics for a method"""

	avg_makespan: float = Field(..., description='Average makespan')
	std_makespan: float = Field(..., description='Standard deviation of makespan')
	min_makespan: float = Field(..., description='Minimum makespan')
	max_makespan: float = Field(..., description='Maximum makespan')
	avg_reward: float = Field(..., description='Average reward')
	std_reward: float = Field(..., description='Standard deviation of reward')
	avg_execution_time: float = Field(..., description='Average execution time')
	total_episodes: int = Field(..., description='Total episodes')


class ComparisonResult(BaseModel):
	"""Result of JSS comparison"""

	instance_name: str = Field(..., description='Instance name used')
	controller_name: Optional[str] = Field(None, description='Controller name used')
	results: Dict[str, PerformanceMetrics] = Field(..., description='Results by method')
	best_method: str = Field(..., description='Best performing method')
	best_makespan: float = Field(..., description='Best average makespan')
	ranking: List[str] = Field(..., description='Methods ranked by performance')
	execution_summary: Dict[str, Any] = Field(..., description='Execution summary')


class SingleRunResult(BaseModel):
	"""Result of a single JSS run"""

	instance_name: str = Field(..., description='Instance name used')
	controller_name: Optional[str] = Field(None, description='Controller name used')
	agent_type: str = Field(..., description='Agent type used')
	makespan: float = Field(..., description='Final makespan')
	total_reward: float = Field(..., description='Total reward')
	execution_time: float = Field(..., description='Execution time')
	schedule: List[Dict[str, Any]] = Field(..., description='Detailed schedule')


class ScheduleTask(BaseModel):
	"""A task in the schedule"""

	job_id: int = Field(..., description='Job ID')
	machine_id: int = Field(..., description='Machine ID')
	start_time: float = Field(..., description='Start time')
	end_time: float = Field(..., description='End time')
	person_id: Optional[int] = Field(None, description='Person ID (if using controller)')


class ErrorResponse(BaseModel):
	"""Error response model"""

	error: str = Field(..., description='Error message')
	detail: Optional[str] = Field(None, description='Detailed error information')
	code: Optional[int] = Field(None, description='Error code')


class HealthResponse(BaseModel):
	"""Health check response"""

	status: str = Field(..., description='Service status')
	version: str = Field(..., description='API version')
	timestamp: str = Field(..., description='Current timestamp')
	uptime: Optional[float] = Field(None, description='Uptime in seconds')
	available_instances: Optional[int] = Field(None, description='Number of available instances')
	available_controllers: Optional[int] = Field(None, description='Number of available controllers')


class VisualizationRequest(BaseModel):
	"""Request for generating visualizations"""

	instance_name: str = Field(..., description='Name of the JSS instance')
	results_id: str = Field(..., description='ID of the comparison results')
	visualization_types: List[str] = Field(
		default=['dashboard', 'detailed', 'gantt'],
		description='Types of visualizations to generate',
	)
	format: str = Field(default='png', description='Output format for visualizations')


class BackgroundTaskStatus(BaseModel):
	"""Status of a background task"""

	task_id: str = Field(..., description='Task ID')
	status: str = Field(..., description='Task status (pending, running, completed, failed)')
	progress: Optional[float] = Field(None, description='Task progress (0-100)')
	result: Optional[Dict[str, Any]] = Field(None, description='Task result if completed')
	error: Optional[str] = Field(None, description='Error message if failed')
	created_at: datetime = Field(..., description='Task creation time')
	updated_at: datetime = Field(..., description='Last update time')
