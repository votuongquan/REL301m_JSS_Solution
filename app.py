"""
FastAPI application for Job Shop Scheduling (JSS) API
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Import routes
from api.routes.jss_routes import router as jss_router, init_services
from api.routes.file_routes import router as file_router
from api.stream.stream_routes import router as stream_router, init_streaming_service

# Get project root directory
PROJECT_ROOT = Path(__file__).parent
INSTANCES_DIR = PROJECT_ROOT / 'instances'
CONTROLLERS_DIR = PROJECT_ROOT / 'controllers'
RESULTS_DIR = PROJECT_ROOT / 'results'

# Create FastAPI app
app = FastAPI(
	title='Job Shop Scheduling API',
	description='API for running and comparing Job Shop Scheduling algorithms',
	version='1.0.0',
	docs_url='/docs',
	redoc_url='/redoc',
)

# Add CORS middleware
app.add_middleware(
	CORSMiddleware,
	allow_origins=['*'],  # In production, specify actual origins
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*'],
)

# Include routers
app.include_router(jss_router)
app.include_router(file_router)
app.include_router(stream_router)

# Serve static files (results, visualizations)
RESULTS_DIR.mkdir(exist_ok=True)
app.mount('/results', StaticFiles(directory=str(RESULTS_DIR)), name='results')


@app.on_event('startup')
async def startup_event():
	"""Initialize services on startup"""
	# Ensure directories exist
	INSTANCES_DIR.mkdir(exist_ok=True)
	CONTROLLERS_DIR.mkdir(exist_ok=True)
	RESULTS_DIR.mkdir(exist_ok=True)

	# Initialize services with results directory
	init_services(str(INSTANCES_DIR), str(CONTROLLERS_DIR), str(RESULTS_DIR))
	
	# Initialize streaming service
	from api.routes.jss_routes import get_file_service
	init_streaming_service(get_file_service())

	print('🚀 JSS API started!')
	print(f'📁 Instances directory: {INSTANCES_DIR}')
	print(f'🎛️  Controllers directory: {CONTROLLERS_DIR}')
	print(f'📊 Results directory: {RESULTS_DIR}')
	print('🌊 Streaming service initialized!')


@app.get('/', response_class=HTMLResponse)
async def root():
	"""Root endpoint with API information"""
	html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Job Shop Scheduling API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; text-align: center; }
            .section { margin: 20px 0; }
            .endpoint { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { font-weight: bold; color: #27ae60; }
            .path { font-family: monospace; color: #8e44ad; }
            a { color: #3498db; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .status { background: #d5f4e6; padding: 10px; border-radius: 5px; border-left: 4px solid #27ae60; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏭 Job Shop Scheduling API</h1>
            
            <div class="status">
                <strong>✅ API Status:</strong> Running<br>
                <strong>📖 Documentation:</strong> <a href="/docs">Interactive API Docs</a> | <a href="/redoc">ReDoc</a>
            </div>
            
            <div class="section">
                <h2>🎯 Main Endpoints</h2>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="path">/api/v1/instances</span><br>
                    Get list of available JSS instances (with optional detailed stats)
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="path">/api/v1/controllers</span><br>
                    Get list of available controllers (with optional detailed stats)
                </div>
                  <div class="endpoint">
                    <span class="method">POST</span> <span class="path">/api/v1/compare</span><br>
                    Run comprehensive comparison of JSS methods (synchronous)
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> <span class="path">/api/v1/compare/background</span><br>
                    Run comprehensive comparison in background with task tracking
                </div>
                
                <div class="endpoint">
                    <span class="method">WebSocket</span> <span class="path">/api/v1/stream/ws</span><br>
                    Real-time streaming WebSocket endpoint for live JSS results
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> <span class="path">/api/v1/stream/start</span><br>
                    Start a new streaming comparison with real-time updates
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="path">/api/v1/stream/sessions</span><br>
                    Get all streaming sessions and their status
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="path">/api/v1/tasks</span><br>
                    Get all background tasks and their status
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="path">/api/v1/tasks/{task_id}</span><br>
                    Get status of a specific background task
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> <span class="path">/api/v1/visualizations</span><br>
                    Generate visualizations for comparison results
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="path">/api/v1/files</span><br>
                    List result files and visualizations
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="path">/api/v1/files/download/{file_path}</span><br>
                    Download result files and visualizations
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> <span class="path">/api/v1/run</span><br>
                    Run a single JSS episode
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="path">/api/v1/health</span><br>
                    Health check endpoint with system stats
                </div>
            </div>
            
            <div class="section">
                <h2>🔧 Available Agents</h2>
                <ul>
                    <li><strong>hybrid</strong> - Hybrid Priority Scoring Agent</li>
                    <li><strong>lookahead</strong> - Adaptive Look-ahead Agent</li>
                    <li><strong>controller</strong> - Controller-constrained Agent</li>
                </ul>
            </div>
              <div class="section">
                <h2>📊 Features</h2>
                <ul>
                    <li>Multiple JSS algorithm comparison</li>
                    <li>Custom agent implementations (Hybrid, LookAhead, Controller-constrained)</li>
                    <li>Background task processing with progress tracking</li>
                    <li><strong>🌊 Real-time streaming with WebSocket support</strong></li>
                    <li>Live episode-by-episode progress updates</li>
                    <li>Detailed instance and controller statistics</li>
                    <li>Automatic visualization generation (dashboards, Gantt charts)</li>
                    <li>File management and download capabilities</li>
                    <li>Performance metrics and analysis</li>
                    <li>RESTful API with comprehensive documentation</li>
                    <li>Health monitoring with system statistics</li>
                </ul>
            </div>
              <div class="section">
                <h2>🚀 Quick Start</h2>
                <p>1. View available instances: <code>GET /api/v1/instances</code></p>
                <p>2. Run a quick comparison: <code>POST /api/v1/compare</code></p>
                <p>3. Start streaming comparison: <code>POST /api/v1/stream/start</code></p>
                <p>4. Connect to WebSocket: <code>ws://localhost:8000/api/v1/stream/ws</code></p>
                <p>5. Check the <a href="/docs">interactive documentation</a> for detailed API usage</p>
                <p>6. View streaming example: <a href="/api/v1/stream/example-client">JavaScript client example</a></p>
            </div>
        </div>
    </body>
    </html>
    """
	return html_content


if __name__ == '__main__':
	# Run with uvicorn
	uvicorn.run('app:app', host='0.0.0.0', port=8000, reload=True, log_level='info')
