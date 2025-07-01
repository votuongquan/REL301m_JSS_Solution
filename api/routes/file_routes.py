"""
File management and visualization routes
"""

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from api.routes.jss_routes import get_file_service
from api.services.jss_service import JSSFileService

# Create router
router = APIRouter(prefix='/api/v1/files', tags=['File Management'])


@router.post('/instances/upload')
async def upload_instance(file: UploadFile = File(...), fs: JSSFileService = Depends(get_file_service)):
	"""Upload a new JSS instance file"""
	try:
		# Validate file
		if not file.filename:
			raise HTTPException(status_code=400, detail='No filename provided')

		# Check if instance already exists
		if fs.instance_exists(file.filename):
			raise HTTPException(status_code=409, detail=f"Instance '{file.filename}' already exists")

		# Save file
		instance_path = fs.instances_dir / file.filename

		async with aiofiles.open(instance_path, 'wb') as f:
			content = await file.read()
			await f.write(content)

		return {
			'message': f"Instance '{file.filename}' uploaded successfully",
			'path': str(instance_path),
		}

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Failed to upload instance: {str(e)}')


@router.post('/controllers/upload')
async def upload_controller(file: UploadFile = File(...), fs: JSSFileService = Depends(get_file_service)):
	"""Upload a new controller file"""
	try:
		# Validate file
		if not file.filename:
			raise HTTPException(status_code=400, detail='No filename provided')

		if not file.filename.endswith('.txt'):
			raise HTTPException(status_code=400, detail='Controller file must be a .txt file')

		controller_name = file.filename[:-4]  # Remove .txt extension

		# Check if controller already exists
		if fs.controller_exists(controller_name):
			raise HTTPException(status_code=409, detail=f"Controller '{controller_name}' already exists")

		# Save file
		controller_path = fs.controllers_dir / file.filename

		async with aiofiles.open(controller_path, 'wb') as f:
			content = await file.read()
			await f.write(content)

		return {
			'message': f"Controller '{controller_name}' uploaded successfully",
			'path': str(controller_path),
		}

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Failed to upload controller: {str(e)}')


@router.delete('/instances/{instance_name}')
async def delete_instance(instance_name: str, fs: JSSFileService = Depends(get_file_service)):
	"""Delete an instance file"""
	try:
		if not fs.instance_exists(instance_name):
			raise HTTPException(status_code=404, detail=f"Instance '{instance_name}' not found")

		instance_path = fs.instances_dir / instance_name
		instance_path.unlink()

		return {'message': f"Instance '{instance_name}' deleted successfully"}

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Failed to delete instance: {str(e)}')


@router.delete('/controllers/{controller_name}')
async def delete_controller(controller_name: str, fs: JSSFileService = Depends(get_file_service)):
	"""Delete a controller file"""
	try:
		if not fs.controller_exists(controller_name):
			raise HTTPException(status_code=404, detail=f"Controller '{controller_name}' not found")

		controller_path = fs.controllers_dir / f'{controller_name}.txt'
		controller_path.unlink()

		return {'message': f"Controller '{controller_name}' deleted successfully"}

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Failed to delete controller: {str(e)}')


@router.get('/instances/{instance_name}/download')
async def download_instance(instance_name: str, fs: JSSFileService = Depends(get_file_service)):
	"""Download an instance file"""
	try:
		if not fs.instance_exists(instance_name):
			raise HTTPException(status_code=404, detail=f"Instance '{instance_name}' not found")

		instance_path = fs.instances_dir / instance_name

		return FileResponse(
			path=str(instance_path),
			filename=instance_name,
			media_type='application/octet-stream',
		)

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Failed to download instance: {str(e)}')


@router.get('/controllers/{controller_name}/download')
async def download_controller(controller_name: str, fs: JSSFileService = Depends(get_file_service)):
	"""Download a controller file"""
	try:
		if not fs.controller_exists(controller_name):
			raise HTTPException(status_code=404, detail=f"Controller '{controller_name}' not found")

		controller_path = fs.controllers_dir / f'{controller_name}.txt'

		return FileResponse(
			path=str(controller_path),
			filename=f'{controller_name}.txt',
			media_type='text/plain',
		)

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Failed to download controller: {str(e)}')
