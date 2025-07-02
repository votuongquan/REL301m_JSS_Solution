"""
JSS Streaming Service - Business logic for WebSocket streaming
"""

import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from api.services.jss_service import JSSFileService
from api.schemas.stream_schemas import (
    StreamAgentType,
    StreamComparisonRequest,
    StreamDispatchingRule,
    StreamMethodResult,
    StreamResults,
    StreamSessionInfo,
    StreamStats,
)
from comparison_framework.stream.stream_agents import (
    create_stream_agent,
    create_dispatching_rule_agent,
)
from comparison_framework.stream.stream_framework import StreamJSSFramework
from comparison_framework.stream.stream_manager import StreamManager

logger = logging.getLogger(__name__)


class JSSStreamingService:
    """Service for managing JSS streaming operations"""

    def __init__(self, file_service: JSSFileService, stream_manager: StreamManager):
        self.file_service = file_service
        self.stream_manager = stream_manager
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.start_time = time.time()

    async def start_comparison_stream(self, request: StreamComparisonRequest) -> str:
        """Start a new streaming comparison"""
        
        # Validate instance exists
        if not self.file_service.instance_exists(request.instance_name):
            raise ValueError(f"Instance '{request.instance_name}' not found")

        # Validate controller if specified
        if request.controller_name and not self.file_service.controller_exists(request.controller_name):
            raise ValueError(f"Controller '{request.controller_name}' not found")

        # Create session
        session_id = await self.stream_manager.create_session(request.dict())

        # Start background task
        task = asyncio.create_task(
            self._run_comparison_background(session_id, request)
        )
        self.active_tasks[session_id] = task

        return session_id

    async def _run_comparison_background(self, session_id: str, request: StreamComparisonRequest):
        """Run comparison in background with streaming updates"""
        
        try:
            # Update session status
            await self.stream_manager.update_session_status(session_id, "running")

            # Get instance path
            instance_path = self.file_service.get_instance_path(request.instance_name)

            # Create streaming framework
            framework = StreamJSSFramework(instance_path)

            # Test environment first
            env_test_success = await framework.test_environment()
            if not env_test_success:
                await self.stream_manager.send_error(
                    session_id, 
                    "Failed to create JSS environment",
                    {"instance_path": instance_path}
                )
                return

            # Create agents
            agents = []
            for agent_type in request.agents:
                try:
                    if agent_type == StreamAgentType.CONTROLLER:
                        if not request.controller_name:
                            raise ValueError("Controller name required for controller agent")
                        
                        controller_path = self.file_service.get_controller_path(request.controller_name)
                        agent = create_stream_agent(
                            agent_type.value,
                            controller_path=controller_path,
                            num_people=request.num_people
                        )
                    elif agent_type == StreamAgentType.LOOKAHEAD:
                        agent = create_stream_agent(
                            agent_type.value,
                            lookahead_depth=request.lookahead_depth or 2
                        )
                    else:
                        agent = create_stream_agent(agent_type.value)
                    
                    agents.append(agent)
                    
                except Exception as e:
                    logger.error(f"Failed to create agent {agent_type}: {e}")
                    await self.stream_manager.send_error(
                        session_id,
                        f"Failed to create agent {agent_type}",
                        {"error": str(e)}
                    )

            # Create streaming callback
            async def stream_callback(event_type: str, **kwargs):
                try:
                    if event_type == 'comparison_start':
                        # Send comparison start event
                        await self.stream_manager.broadcast_to_session_subscribers(
                            session_id,
                            {
                                'type': 'comparison_start',
                                'session_id': session_id,
                                'total_methods': kwargs.get('total_methods', 0),
                                'total_episodes_per_method': kwargs.get('total_episodes_per_method', 0),
                                'timestamp': datetime.now().isoformat()
                            }
                        )

                    elif event_type == 'method_start':
                        await self.stream_manager.broadcast_to_session_subscribers(
                            session_id,
                            {
                                'type': 'method_start',
                                'session_id': session_id,
                                'method_name': kwargs.get('method_name'),
                                'method_type': kwargs.get('method_type'),
                                'completed_methods': kwargs.get('completed_methods', 0),
                                'total_methods': kwargs.get('total_methods', 0),
                                'timestamp': datetime.now().isoformat()
                            }
                        )

                    elif event_type == 'episode_start':
                        await self.stream_manager.send_episode_start(
                            session_id,
                            kwargs.get('episode', 0),
                            kwargs.get('agent_name', 'Unknown')
                        )

                    elif event_type == 'episode_progress':
                        step = kwargs.get('step', 0)
                        # Only send progress updates every few steps to avoid overwhelming
                        if step % 5 == 0:  # Every 5 steps
                            await self.stream_manager.send_episode_progress(
                                session_id,
                                kwargs.get('episode', 0),
                                kwargs.get('agent_name', 'Unknown'),
                                step,
                                kwargs.get('action', 0),
                                kwargs.get('reward', 0),
                                kwargs.get('current_makespan')
                            )

                    elif event_type == 'episode_complete':
                        await self.stream_manager.send_episode_complete(
                            session_id,
                            kwargs.get('episode', 0),
                            kwargs.get('agent_name', 'Unknown'),
                            kwargs.get('makespan', 0),
                            kwargs.get('total_reward', 0),
                            kwargs.get('execution_time', 0)
                        )

                    elif event_type == 'method_complete':
                        await self.stream_manager.broadcast_to_session_subscribers(
                            session_id,
                            {
                                'type': 'method_complete',
                                'session_id': session_id,
                                'method_name': kwargs.get('method_name'),
                                'results': kwargs.get('results', {}),
                                'completed_methods': kwargs.get('completed_methods', 0),
                                'total_methods': kwargs.get('total_methods', 0),
                                'timestamp': datetime.now().isoformat()
                            }
                        )

                    elif event_type == 'comparison_complete':
                        results = kwargs.get('results', {})
                        await self.stream_manager.send_comparison_complete(session_id, results)

                    elif event_type == 'error':
                        await self.stream_manager.send_error(
                            session_id,
                            kwargs.get('error_message', 'Unknown error'),
                            kwargs
                        )

                except Exception as e:
                    logger.error(f"Error in stream callback: {e}")

            # Run comprehensive comparison
            results = await framework.run_comprehensive_comparison_stream(
                custom_agents=agents,
                dispatching_rules=[rule.value for rule in request.dispatching_rules],
                num_episodes=request.num_episodes,
                include_random=request.include_random_baseline,
                stream_callback=stream_callback
            )

            # Update final session status
            await self.stream_manager.update_session_status(
                session_id, 
                "completed",
                results=results
            )

        except Exception as e:
            logger.error(f"Error in comparison stream {session_id}: {e}")
            await self.stream_manager.send_error(
                session_id,
                f"Comparison failed: {str(e)}",
                {"traceback": str(e)}
            )
            await self.stream_manager.update_session_status(
                session_id,
                "failed",
                error_message=str(e)
            )

        finally:
            # Clean up task
            if session_id in self.active_tasks:
                del self.active_tasks[session_id]

    async def get_session_info(self, session_id: str) -> Optional[StreamSessionInfo]:
        """Get information about a streaming session"""
        session_data = self.stream_manager.get_session_info(session_id)
        if session_data:
            return StreamSessionInfo(**session_data)
        return None

    async def get_all_sessions(self) -> List[StreamSessionInfo]:
        """Get information about all sessions"""
        sessions_data = self.stream_manager.get_all_sessions()
        return [StreamSessionInfo(**session) for session in sessions_data]

    async def cancel_session(self, session_id: str) -> bool:
        """Cancel a running session"""
        if session_id in self.active_tasks:
            task = self.active_tasks[session_id]
            task.cancel()
            
            await self.stream_manager.update_session_status(
                session_id,
                "cancelled"
            )
            
            return True
        return False

    async def get_streaming_stats(self) -> StreamStats:
        """Get current streaming statistics"""
        all_sessions = await self.get_all_sessions()
        active_sessions = len([s for s in all_sessions if s.status == "running"])
        
        return StreamStats(
            total_sessions=len(all_sessions),
            active_sessions=active_sessions,
            total_connections=self.stream_manager.get_connection_count()
        )

    async def convert_results_to_stream_format(self, results: Dict) -> StreamResults:
        """Convert framework results to streaming format"""
        
        method_results = {}
        best_method = None
        best_makespan = float('inf')
        
        for method_name, method_data in results.items():
            if method_name.startswith('_'):  # Skip meta fields
                continue
                
            method_result = StreamMethodResult(
                method_name=method_name,
                method_type=self._get_method_type(method_name),
                episodes_completed=method_data.get('episodes_completed', 0),
                avg_makespan=method_data.get('avg_makespan', 0),
                best_makespan=method_data.get('best_makespan', 0),
                worst_makespan=method_data.get('worst_makespan', 0),
                std_makespan=method_data.get('std_makespan', 0),
                avg_reward=method_data.get('avg_reward', 0),
                avg_execution_time=method_data.get('avg_execution_time', 0)
            )
            
            method_results[method_name] = method_result
            
            # Track best method
            if method_result.avg_makespan < best_makespan:
                best_makespan = method_result.avg_makespan
                best_method = method_name
        
        return StreamResults(
            session_id="",  # Will be set by caller
            instance_name="",  # Will be set by caller
            total_methods=len(method_results),
            results=method_results,
            best_method=best_method,
            best_makespan=best_makespan if best_makespan != float('inf') else None
        )

    def _get_method_type(self, method_name: str) -> str:
        """Determine method type from method name"""
        if method_name in ['SPT', 'FIFO', 'MWR', 'LWR', 'MOR', 'LOR', 'CR']:
            return 'dispatching_rule'
        elif method_name == 'Random':
            return 'random'
        else:
            return 'agent'

    async def cleanup_finished_tasks(self):
        """Clean up finished background tasks"""
        finished_tasks = []
        
        for session_id, task in self.active_tasks.items():
            if task.done():
                finished_tasks.append(session_id)
        
        for session_id in finished_tasks:
            del self.active_tasks[session_id]

    def get_uptime(self) -> float:
        """Get service uptime in seconds"""
        return time.time() - self.start_time
