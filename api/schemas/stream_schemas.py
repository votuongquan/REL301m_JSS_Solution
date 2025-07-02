"""
Pydantic schemas for JSS streaming API
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Literal

from pydantic import BaseModel, Field


class StreamAgentType(str, Enum):
    """Available streaming agent types"""
    HYBRID = 'hybrid'
    LOOKAHEAD = 'lookahead'
    CONTROLLER = 'controller'


class StreamDispatchingRule(str, Enum):
    """Available dispatching rules for streaming"""
    SPT = 'SPT'
    FIFO = 'FIFO'
    MWR = 'MWR'
    LWR = 'LWR'
    MOR = 'MOR'
    LOR = 'LOR'
    CR = 'CR'


class StreamStatus(str, Enum):
    """Stream session status"""
    INITIALIZING = 'initializing'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class StreamEventType(str, Enum):
    """WebSocket event types"""
    CONNECTION_ESTABLISHED = 'connection_established'
    SESSION_CREATED = 'session_created'
    SESSION_SUBSCRIBED = 'session_subscribed'
    SESSION_STATUS_UPDATE = 'session_status_update'
    COMPARISON_START = 'comparison_start'
    COMPARISON_PROGRESS = 'comparison_progress'
    COMPARISON_COMPLETE = 'comparison_complete'
    METHOD_START = 'method_start'
    METHOD_COMPLETE = 'method_complete'
    EPISODE_START = 'episode_start'
    EPISODE_PROGRESS = 'episode_progress'
    EPISODE_COMPLETE = 'episode_complete'
    ERROR = 'error'
    PING = 'ping'
    PONG = 'pong'


# Request Models

class StreamComparisonRequest(BaseModel):
    """Request for starting a streaming JSS comparison"""
    
    instance_name: str = Field(..., description='Name of the JSS instance')
    controller_name: Optional[str] = Field(None, description='Controller name (optional)')
    agents: List[StreamAgentType] = Field(default=[StreamAgentType.HYBRID], description='Agents to compare')
    dispatching_rules: List[StreamDispatchingRule] = Field(default=[], description='Dispatching rules to compare')
    num_episodes: int = Field(default=10, ge=1, le=100, description='Number of episodes to run')
    include_random_baseline: bool = Field(default=True, description='Include random baseline')
    
    # Agent-specific parameters
    lookahead_depth: Optional[int] = Field(default=2, ge=1, le=5, description='Lookahead depth for lookahead agent')
    num_people: Optional[int] = Field(None, description='Number of people for controller agent')


class ClientMessage(BaseModel):
    """Message from client to server"""
    
    type: str = Field(..., description='Message type')
    session_id: Optional[str] = Field(None, description='Session ID for subscription messages')
    data: Optional[Dict[str, Any]] = Field(None, description='Additional message data')


# Response Models

class StreamEpisodeResult(BaseModel):
    """Result of a single episode"""
    
    episode: int = Field(..., description='Episode number')
    agent_name: str = Field(..., description='Agent name')
    makespan: float = Field(..., description='Episode makespan')
    total_reward: float = Field(..., description='Total episode reward')
    execution_time: float = Field(..., description='Episode execution time in seconds')


class StreamMethodResult(BaseModel):
    """Results for a complete method evaluation"""
    
    method_name: str = Field(..., description='Method name')
    method_type: str = Field(..., description='Method type (agent/rule/random)')
    episodes_completed: int = Field(..., description='Number of completed episodes')
    avg_makespan: float = Field(..., description='Average makespan')
    best_makespan: float = Field(..., description='Best makespan')
    worst_makespan: float = Field(..., description='Worst makespan')
    std_makespan: float = Field(..., description='Standard deviation of makespan')
    avg_reward: float = Field(..., description='Average reward')
    avg_execution_time: float = Field(..., description='Average execution time')


class StreamSessionInfo(BaseModel):
    """Information about a streaming session"""
    
    session_id: str = Field(..., description='Unique session identifier')
    status: StreamStatus = Field(..., description='Current session status')
    progress: float = Field(..., description='Overall progress (0.0 to 1.0)')
    current_episode: int = Field(..., description='Current episode number')
    total_episodes: int = Field(..., description='Total episodes per method')
    created_at: datetime = Field(..., description='Session creation timestamp')
    request_data: Dict[str, Any] = Field(..., description='Original request data')
    subscriber_count: int = Field(..., description='Number of subscribed clients')
    error_message: Optional[str] = Field(None, description='Error message if failed')


class StreamResults(BaseModel):
    """Complete streaming results"""
    
    session_id: str = Field(..., description='Session ID')
    instance_name: str = Field(..., description='Instance name')
    total_methods: int = Field(..., description='Total number of methods compared')
    results: Dict[str, StreamMethodResult] = Field(..., description='Results by method name')
    best_method: Optional[str] = Field(None, description='Best performing method')
    best_makespan: Optional[float] = Field(None, description='Best makespan achieved')
    comparison_duration: Optional[float] = Field(None, description='Total comparison time in seconds')


# WebSocket Event Models

class BaseStreamEvent(BaseModel):
    """Base model for all streaming events"""
    
    type: StreamEventType = Field(..., description='Event type')
    timestamp: datetime = Field(..., description='Event timestamp')


class ConnectionEstablishedEvent(BaseStreamEvent):
    """Connection established event"""
    
    type: Literal[StreamEventType.CONNECTION_ESTABLISHED] = StreamEventType.CONNECTION_ESTABLISHED
    client_id: str = Field(..., description='Unique client identifier')


class SessionCreatedEvent(BaseStreamEvent):
    """Session created event"""
    
    type: Literal[StreamEventType.SESSION_CREATED] = StreamEventType.SESSION_CREATED
    session: StreamSessionInfo = Field(..., description='Session information')


class SessionStatusUpdateEvent(BaseStreamEvent):
    """Session status update event"""
    
    type: Literal[StreamEventType.SESSION_STATUS_UPDATE] = StreamEventType.SESSION_STATUS_UPDATE
    session_id: str = Field(..., description='Session ID')
    status: StreamStatus = Field(..., description='New status')
    session: StreamSessionInfo = Field(..., description='Updated session information')


class ComparisonStartEvent(BaseStreamEvent):
    """Comparison start event"""
    
    type: Literal[StreamEventType.COMPARISON_START] = StreamEventType.COMPARISON_START
    session_id: str = Field(..., description='Session ID')
    total_methods: int = Field(..., description='Total methods to compare')
    total_episodes_per_method: int = Field(..., description='Episodes per method')


class ComparisonProgressEvent(BaseStreamEvent):
    """Comparison progress event"""
    
    type: Literal[StreamEventType.COMPARISON_PROGRESS] = StreamEventType.COMPARISON_PROGRESS
    session_id: str = Field(..., description='Session ID')
    completed_methods: int = Field(..., description='Number of completed methods')
    total_methods: int = Field(..., description='Total methods')
    current_method: Optional[str] = Field(None, description='Currently running method')
    progress: float = Field(..., description='Overall progress (0.0 to 1.0)')


class ComparisonCompleteEvent(BaseStreamEvent):
    """Comparison complete event"""
    
    type: Literal[StreamEventType.COMPARISON_COMPLETE] = StreamEventType.COMPARISON_COMPLETE
    session_id: str = Field(..., description='Session ID')
    results: Dict[str, Any] = Field(..., description='Complete results')


class MethodStartEvent(BaseStreamEvent):
    """Method evaluation start event"""
    
    type: Literal[StreamEventType.METHOD_START] = StreamEventType.METHOD_START
    session_id: str = Field(..., description='Session ID')
    method_name: str = Field(..., description='Method name')
    method_type: str = Field(..., description='Method type')
    completed_methods: int = Field(..., description='Previously completed methods')
    total_methods: int = Field(..., description='Total methods')


class MethodCompleteEvent(BaseStreamEvent):
    """Method evaluation complete event"""
    
    type: Literal[StreamEventType.METHOD_COMPLETE] = StreamEventType.METHOD_COMPLETE
    session_id: str = Field(..., description='Session ID')
    method_name: str = Field(..., description='Method name')
    results: Dict[str, Any] = Field(..., description='Method results')
    completed_methods: int = Field(..., description='Completed methods count')
    total_methods: int = Field(..., description='Total methods')


class EpisodeStartEvent(BaseStreamEvent):
    """Episode start event"""
    
    type: Literal[StreamEventType.EPISODE_START] = StreamEventType.EPISODE_START
    session_id: str = Field(..., description='Session ID')
    episode: int = Field(..., description='Episode number')
    total_episodes: int = Field(..., description='Total episodes for this method')
    agent_name: str = Field(..., description='Agent name')


class EpisodeProgressEvent(BaseStreamEvent):
    """Episode progress event"""
    
    type: Literal[StreamEventType.EPISODE_PROGRESS] = StreamEventType.EPISODE_PROGRESS
    session_id: str = Field(..., description='Session ID')
    episode: int = Field(..., description='Episode number')
    agent_name: str = Field(..., description='Agent name')
    step: int = Field(..., description='Current step in episode')
    action: int = Field(..., description='Action taken')
    reward: float = Field(..., description='Step reward')
    total_reward: Optional[float] = Field(None, description='Cumulative reward')
    current_makespan: Optional[float] = Field(None, description='Current makespan')


class EpisodeCompleteEvent(BaseStreamEvent):
    """Episode complete event"""
    
    type: Literal[StreamEventType.EPISODE_COMPLETE] = StreamEventType.EPISODE_COMPLETE
    session_id: str = Field(..., description='Session ID')
    episode: int = Field(..., description='Episode number')
    agent_name: str = Field(..., description='Agent name')
    makespan: float = Field(..., description='Final makespan')
    total_reward: float = Field(..., description='Total episode reward')
    execution_time: float = Field(..., description='Episode execution time')
    current_stats: Optional[Dict[str, Any]] = Field(None, description='Current method statistics')


class ErrorEvent(BaseStreamEvent):
    """Error event"""
    
    type: Literal[StreamEventType.ERROR] = StreamEventType.ERROR
    session_id: Optional[str] = Field(None, description='Session ID if applicable')
    error_message: str = Field(..., description='Error message')
    error_details: Optional[Dict[str, Any]] = Field(None, description='Additional error details')
    method_name: Optional[str] = Field(None, description='Method name if applicable')
    episode: Optional[int] = Field(None, description='Episode number if applicable')


# Union type for all possible events
StreamEvent = Union[
    ConnectionEstablishedEvent,
    SessionCreatedEvent,
    SessionStatusUpdateEvent,
    ComparisonStartEvent,
    ComparisonProgressEvent,
    ComparisonCompleteEvent,
    MethodStartEvent,
    MethodCompleteEvent,
    EpisodeStartEvent,
    EpisodeProgressEvent,
    EpisodeCompleteEvent,
    ErrorEvent
]


# Additional utility models

class StreamStats(BaseModel):
    """Current streaming statistics"""
    
    total_sessions: int = Field(..., description='Total number of sessions')
    active_sessions: int = Field(..., description='Currently active sessions')
    total_connections: int = Field(..., description='Total active WebSocket connections')
    
    
class HealthCheck(BaseModel):
    """Health check response for streaming API"""
    
    status: str = Field(..., description='Health status')
    timestamp: datetime = Field(..., description='Check timestamp')
    active_connections: int = Field(..., description='Active WebSocket connections')
    active_sessions: int = Field(..., description='Active streaming sessions')
    uptime_seconds: float = Field(..., description='Server uptime in seconds')
