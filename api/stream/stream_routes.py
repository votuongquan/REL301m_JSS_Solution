"""
WebSocket Routes for JSS Streaming
Real-time streaming of JSS comparison results
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from api.routes.jss_routes import get_file_service
from api.services.jss_service import JSSFileService
from api.stream.stream_schemas import (
    ClientMessage,
    HealthCheck,
    StreamComparisonRequest,
    StreamSessionInfo,
    StreamStats,
)
from api.stream.stream_service import JSSStreamingService
from comparison_framework.stream.stream_manager import stream_manager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix='/api/v1/stream', tags=['JSS Streaming'])

# Global streaming service
streaming_service: Optional[JSSStreamingService] = None


def get_streaming_service() -> JSSStreamingService:
    """Dependency to get streaming service"""
    if streaming_service is None:
        raise HTTPException(status_code=500, detail='Streaming service not initialized')
    return streaming_service


def init_streaming_service(file_service: JSSFileService):
    """Initialize streaming service"""
    global streaming_service
    streaming_service = JSSStreamingService(file_service, stream_manager)


# WebSocket endpoint
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for streaming"""
    client_id = None
    
    try:
        # Connect client
        client_id = await stream_manager.connect_client(websocket)
        logger.info(f"WebSocket client {client_id} connected")

        # Listen for messages
        while True:
            try:
                # Check if connection is still active
                connection = stream_manager.connections.get(client_id)
                if not connection or not connection.is_active:
                    logger.info(f"Connection {client_id} is no longer active, breaking loop")
                    break
                
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle client message
                await stream_manager.handle_client_message(client_id, message_data)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket client {client_id} disconnected during receive")
                break
                
            except json.JSONDecodeError:
                # Send error for invalid JSON if connection is still active
                if connection and connection.is_active:
                    await stream_manager.send_to_client(client_id, {
                        'type': 'error',
                        'error_message': 'Invalid JSON format',
                        'timestamp': datetime.now().isoformat()
                    })
            
            except Exception as e:
                logger.error(f"Error handling message from {client_id}: {e}")
                # Send error if connection is still active
                if connection and connection.is_active:
                    await stream_manager.send_to_client(client_id, {
                        'type': 'error',
                        'error_message': 'Internal server error',
                        'timestamp': datetime.now().isoformat()
                    })
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    
    finally:
        # Clean up connection
        if client_id:
            await stream_manager.disconnect_client(client_id)


# REST endpoints for streaming management

@router.post("/start", response_model=dict)
async def start_streaming_comparison(
    request: StreamComparisonRequest,
    service: JSSStreamingService = Depends(get_streaming_service)
):
    """Start a new streaming comparison"""
    try:
        session_id = await service.start_comparison_stream(request)
        
        return {
            'success': True,
            'session_id': session_id,
            'message': 'Streaming comparison started',
            'websocket_url': f'/api/v1/stream/ws',
            'subscribe_message': {
                'type': 'subscribe',
                'session_id': session_id
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting streaming comparison: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start comparison: {str(e)}")


@router.get("/sessions", response_model=List[StreamSessionInfo])
async def get_streaming_sessions(
    service: JSSStreamingService = Depends(get_streaming_service)
):
    """Get information about all streaming sessions"""
    try:
        sessions = await service.get_all_sessions()
        return sessions
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")


@router.get("/sessions/{session_id}", response_model=StreamSessionInfo)
async def get_streaming_session(
    session_id: str,
    service: JSSStreamingService = Depends(get_streaming_service)
):
    """Get information about a specific streaming session"""
    try:
        session = await service.get_session_info(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@router.post("/sessions/{session_id}/cancel")
async def cancel_streaming_session(
    session_id: str,
    service: JSSStreamingService = Depends(get_streaming_service)
):
    """Cancel a running streaming session"""
    try:
        success = await service.cancel_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or not running")
        
        return {
            'success': True,
            'message': f'Session {session_id} cancelled'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel session: {str(e)}")


@router.get("/stats", response_model=StreamStats)
async def get_streaming_stats(
    service: JSSStreamingService = Depends(get_streaming_service)
):
    """Get current streaming statistics"""
    try:
        stats = await service.get_streaming_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting streaming stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/health", response_model=HealthCheck)
async def stream_health_check(
    service: JSSStreamingService = Depends(get_streaming_service)
):
    """Health check for streaming service"""
    try:
        stats = await service.get_streaming_stats()
        
        return HealthCheck(
            status="healthy",
            timestamp=datetime.now(),
            active_connections=stats.total_connections,
            active_sessions=stats.active_sessions,
            uptime_seconds=service.get_uptime()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            status="unhealthy",
            timestamp=datetime.now(),
            active_connections=0,
            active_sessions=0,
            uptime_seconds=0
        )


@router.post("/cleanup")
async def cleanup_streaming_service(
    service: JSSStreamingService = Depends(get_streaming_service)
):
    """Clean up finished tasks and inactive connections"""
    try:
        # Clean up finished tasks
        await service.cleanup_finished_tasks()
        
        # Clean up inactive connections
        await stream_manager.cleanup_inactive_connections()
        
        return {
            'success': True,
            'message': 'Cleanup completed'
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


# Background task to periodically clean up
async def periodic_cleanup():
    """Periodic cleanup task"""
    while True:
        try:
            if streaming_service:
                await streaming_service.cleanup_finished_tasks()
                await stream_manager.cleanup_inactive_connections()
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")
        
        # Wait 5 minutes
        await asyncio.sleep(300)


# Example client usage endpoint
@router.get("/example-client")
async def get_example_client():
    """Get example JavaScript client code for connecting to streaming"""
    
    example_code = '''
// Example JavaScript WebSocket client for JSS Streaming

class JSSStreamingClient {
    constructor(wsUrl = 'ws://localhost:8000/api/v1/stream/ws') {
        this.wsUrl = wsUrl;
        this.ws = null;
        this.clientId = null;
        this.subscriptions = new Set();
        
        // Event handlers
        this.onConnection = null;
        this.onSessionUpdate = null;
        this.onEpisodeProgress = null;
        this.onError = null;
    }
    
    connect() {
        this.ws = new WebSocket(this.wsUrl);
        
        this.ws.onopen = () => {
            console.log('Connected to JSS streaming server');
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };
        
        this.ws.onclose = () => {
            console.log('Disconnected from streaming server');
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    handleMessage(message) {
        switch (message.type) {
            case 'connection_established':
                this.clientId = message.client_id;
                if (this.onConnection) this.onConnection(message);
                break;
                
            case 'episode_progress':
                if (this.onEpisodeProgress) this.onEpisodeProgress(message);
                break;
                
            case 'session_status_update':
                if (this.onSessionUpdate) this.onSessionUpdate(message);
                break;
                
            case 'error':
                if (this.onError) this.onError(message);
                break;
                
            default:
                console.log('Received message:', message);
        }
    }
    
    subscribeToSession(sessionId) {
        this.send({
            type: 'subscribe',
            session_id: sessionId
        });
        this.subscriptions.add(sessionId);
    }
    
    unsubscribeFromSession(sessionId) {
        this.send({
            type: 'unsubscribe',
            session_id: sessionId
        });
        this.subscriptions.delete(sessionId);
    }
    
    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Usage example:
const client = new JSSStreamingClient();

client.onConnection = (message) => {
    console.log('Connected with client ID:', message.client_id);
};

client.onEpisodeProgress = (message) => {
    console.log(`Episode ${message.episode} progress: step ${message.step}, reward: ${message.reward}`);
};

client.onSessionUpdate = (message) => {
    console.log('Session update:', message.session);
};

client.onError = (message) => {
    console.error('Error:', message.error_message);
};

// Connect and subscribe to a session
client.connect();

// After starting a comparison, subscribe to its session
// client.subscribeToSession('session-id-here');
'''
    
    return JSONResponse(
        content={'example_code': example_code},
        headers={'Content-Type': 'application/json'}
    )
