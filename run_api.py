#!/usr/bin/env python3
"""
Startup script for JSS FastAPI application
"""

if __name__ == '__main__':
	import uvicorn

	print('🚀 Starting Job Shop Scheduling API...')
	print('📖 Documentation will be available at: http://localhost:8081/docs')
	print('🌐 API will be running at: http://localhost:8081')

	uvicorn.run('app:app', host='0.0.0.0', port=8081, reload=True, log_level='info')
