"""
JSS API Routes - Main endpoints for JSS operations
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from api.schemas.jss_schemas import (
	BackgroundTaskStatus,
	ComparisonRequest,
	ComparisonResult,
	ControllerInfo,
	HealthResponse,
	InstanceInfo,
	SingleRunRequest,
	SingleRunResult,
	VisualizationRequest,
)
from api.services.jss_service import JSSExecutionService, JSSFileService

# Create router
router = APIRouter(prefix='/api/v1', tags=['JSS Operations'])

# Global services (will be initialized in main app)
file_service: Optional[JSSFileService] = None
execution_service: Optional[JSSExecutionService] = None


def get_file_service() -> JSSFileService:
	"""Dependency to get file service"""
	if file_service is None:
		raise HTTPException(status_code=500, detail='Service not initialized')
	return file_service


def get_execution_service() -> JSSExecutionService:
	"""Dependency to get execution service"""
	if execution_service is None:
		raise HTTPException(status_code=500, detail='Service not initialized')
	return execution_service


@router.get('/health', response_model=HealthResponse)
async def health_check(fs: JSSFileService = Depends(get_file_service)):
	"""Health check endpoint"""
	from datetime import datetime

	# Get counts for health info
	instances_count = len(fs.get_instances())
	controllers_count = len(fs.get_controllers())

	return HealthResponse(
		status='healthy',
		version='1.0.0',
		timestamp=datetime.now().isoformat(),
		available_instances=instances_count,
		available_controllers=controllers_count,
	)


@router.get('/instances', response_model=List[InstanceInfo])
async def get_instances(
	include_stats: bool = Query(False, description='Include detailed statistics'),
	fs: JSSFileService = Depends(get_file_service),
):
	"""Get list of available JSS instances"""
	try:
		return fs.get_instances(include_stats=include_stats)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Failed to get instances: {str(e)}')


@router.get('/controllers', response_model=List[ControllerInfo])
async def get_controllers(
	include_stats: bool = Query(False, description='Include detailed statistics'),
	fs: JSSFileService = Depends(get_file_service),
):
	"""Get list of available controllers"""
	try:
		return fs.get_controllers(include_stats=include_stats)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Failed to get controllers: {str(e)}')


@router.post('/compare', response_model=ComparisonResult)
async def run_comparison(request: ComparisonRequest, es: JSSExecutionService = Depends(get_execution_service)):
	"""Run comprehensive comparison of JSS methods"""
	try:
		result = await es.run_comparison(request)
		return result
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Comparison failed: {str(e)}')


@router.post('/compare/background')
async def run_comparison_background(request: ComparisonRequest, es: JSSExecutionService = Depends(get_execution_service)):
	"""Run comprehensive comparison in background"""
	try:
		task_id = await es.run_comparison_background(request)
		return {'task_id': task_id, 'status': 'started'}
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Failed to start comparison: {str(e)}')


@router.get('/tasks/{task_id}', response_model=BackgroundTaskStatus)
async def get_task_status(task_id: str, es: JSSExecutionService = Depends(get_execution_service)):
	"""Get status of a background task"""
	task = es.get_task_status(task_id)
	if not task:
		raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
	return task


@router.get('/tasks', response_model=List[BackgroundTaskStatus])
async def get_all_tasks(es: JSSExecutionService = Depends(get_execution_service)):
	"""Get all background tasks"""
	return es.get_all_tasks()


@router.post('/visualizations')
async def generate_visualizations(
	request: VisualizationRequest,
	es: JSSExecutionService = Depends(get_execution_service),
):
	"""Generate visualizations for comparison results"""
	try:
		visualization_paths = await es.generate_visualizations(request)
		return {'visualization_paths': visualization_paths}
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Failed to generate visualizations: {str(e)}')


@router.get('/files')
async def list_result_files(
	pattern: Optional[str] = Query(None, description='Filter files by pattern'),
	es: JSSExecutionService = Depends(get_execution_service),
):
	"""List result files"""
	try:
		files = es.list_result_files(pattern)
		return {'files': files}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Failed to list files: {str(e)}')


@router.get('/files/download/{file_path:path}')
async def download_file(file_path: str, es: JSSExecutionService = Depends(get_execution_service)):
	"""Download a result file"""
	try:
		full_path = es.get_file_path(file_path)
		filename = file_path.split('/')[-1]
		return FileResponse(path=full_path, filename=filename, media_type='application/octet-stream')
	except FileNotFoundError:
		raise HTTPException(status_code=404, detail=f'File not found: {file_path}')
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Failed to download file: {str(e)}')


@router.post('/run', response_model=SingleRunResult)
async def run_single_episode(request: SingleRunRequest, es: JSSExecutionService = Depends(get_execution_service)):
	"""Run a single JSS episode"""
	try:
		result = await es.run_single_episode(request)
		return result
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Execution failed: {str(e)}')


@router.get('/instances/{instance_name}/info')
async def get_instance_info(instance_name: str, fs: JSSFileService = Depends(get_file_service)):
	"""Get detailed information about a specific instance"""
	try:
		if not fs.instance_exists(instance_name):
			raise HTTPException(status_code=404, detail=f"Instance '{instance_name}' not found")

		instances = fs.get_instances()
		instance = next((i for i in instances if i.name == instance_name), None)
		if not instance:
			raise HTTPException(status_code=404, detail=f"Instance '{instance_name}' not found")

		return instance
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Failed to get instance info: {str(e)}')


@router.get('/controllers/{controller_name}/info')
async def get_controller_info(controller_name: str, fs: JSSFileService = Depends(get_file_service)):
	"""Get detailed information about a specific controller"""
	try:
		if not fs.controller_exists(controller_name):
			raise HTTPException(status_code=404, detail=f"Controller '{controller_name}' not found")

		controllers = fs.get_controllers()
		controller = next((c for c in controllers if c.name == controller_name), None)
		if not controller:
			raise HTTPException(status_code=404, detail=f"Controller '{controller_name}' not found")

		return controller
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Failed to get controller info: {str(e)}')


# Initialize services (to be called from main app)
def init_services(instances_dir: str, controllers_dir: str, results_dir: str = None):
	"""Initialize services with directory paths"""
	global file_service, execution_service
	file_service = JSSFileService(instances_dir, controllers_dir, results_dir)
	execution_service = JSSExecutionService(file_service)
