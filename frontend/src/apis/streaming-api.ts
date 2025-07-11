/**
 * JSS Streaming API - WebSocket-based real-time JSS operations
 * Provides streaming capabilities for JSS comparisons with real-time updates
 */

import { handleDirectApiCall } from '@/utils/apiHandler';
import axiosInstance from './axiosInstance';

// Streaming-specific types
export enum StreamStatus {
  INITIALIZING = 'initializing',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export enum StreamEventType {
  CONNECTION_ESTABLISHED = 'connection_established',
  SESSION_CREATED = 'session_created',
  SESSION_SUBSCRIBED = 'session_subscribed',
  SESSION_STATUS_UPDATE = 'session_status_update',
  COMPARISON_START = 'comparison_start',
  COMPARISON_PROGRESS = 'comparison_progress',
  COMPARISON_COMPLETE = 'comparison_complete',
  METHOD_START = 'method_start',
  METHOD_COMPLETE = 'method_complete',
  EPISODE_START = 'episode_start',
  EPISODE_PROGRESS = 'episode_progress',
  EPISODE_COMPLETE = 'episode_complete',
  ERROR = 'error',
  PING = 'ping',
  PONG = 'pong',
}

export interface StreamComparisonRequest {
  instance_name: string;
  controller_name?: string;
  agents: string[];
  dispatching_rules: string[];
  num_episodes: number;
  include_random_baseline: boolean;
  lookahead_depth?: number;
  num_people?: number;
}

export interface StreamSessionInfo {
  session_id: string;
  status: StreamStatus;
  progress: number;
  current_episode: number;
  total_episodes: number;
  created_at: string;
  request_data: StreamComparisonRequest;
  subscriber_count: number;
  error_message?: string;
}

export interface StreamMethodResult {
  method_name: string;
  method_type: string;
  episodes_completed: number;
  avg_makespan: number;
  best_makespan: number;
  worst_makespan: number;
  std_makespan: number;
  avg_reward: number;
  avg_execution_time: number;
}

export interface StreamResults {
  session_id: string;
  instance_name: string;
  total_methods: number;
  results: Record<string, StreamMethodResult>;
  best_method?: string;
  best_makespan?: number;
  comparison_duration?: number;
}

// Event interfaces
export interface BaseStreamEvent {
  type: StreamEventType;
  timestamp: string;
}

export interface ConnectionEstablishedEvent extends BaseStreamEvent {
  type: StreamEventType.CONNECTION_ESTABLISHED;
  client_id: string;
}

export interface SessionCreatedEvent extends BaseStreamEvent {
  type: StreamEventType.SESSION_CREATED;
  session: StreamSessionInfo;
}

export interface ComparisonStartEvent extends BaseStreamEvent {
  type: StreamEventType.COMPARISON_START;
  session_id: string;
  total_methods: number;
  total_episodes_per_method: number;
}

export interface EpisodeProgressEvent extends BaseStreamEvent {
  type: StreamEventType.EPISODE_PROGRESS;
  session_id: string;
  episode: number;
  agent_name: string;
  step: number;
  action: number;
  reward: number;
  total_reward?: number;
  current_makespan?: number;
}

export interface EpisodeCompleteEvent extends BaseStreamEvent {
  type: StreamEventType.EPISODE_COMPLETE;
  session_id: string;
  episode: number;
  agent_name: string;
  makespan: number;
  total_reward: number;
  execution_time: number;
  current_stats?: Record<string, number>;
}

export interface MethodCompleteEvent extends BaseStreamEvent {
  type: StreamEventType.METHOD_COMPLETE;
  session_id: string;
  method_name: string;
  results: StreamMethodResult;
  completed_methods: number;
  total_methods: number;
}

export interface ComparisonCompleteEvent extends BaseStreamEvent {
  type: StreamEventType.COMPARISON_COMPLETE;
  session_id: string;
  results: Record<string, StreamMethodResult>;
}

export interface ErrorEvent extends BaseStreamEvent {
  type: StreamEventType.ERROR;
  session_id?: string;
  error_message: string;
  error_details?: Record<string, unknown>;
  method_name?: string;
  episode?: number;
}

export type StreamEvent = 
  | ConnectionEstablishedEvent
  | SessionCreatedEvent
  | ComparisonStartEvent
  | EpisodeProgressEvent
  | EpisodeCompleteEvent
  | MethodCompleteEvent
  | ComparisonCompleteEvent
  | ErrorEvent;

// Event handlers
export type StreamEventHandler = (event: StreamEvent) => void;

export interface StreamEventHandlers {
  onConnection?: (event: ConnectionEstablishedEvent) => void;
  onSessionCreated?: (event: SessionCreatedEvent) => void;
  onComparisonStart?: (event: ComparisonStartEvent) => void;
  onEpisodeProgress?: (event: EpisodeProgressEvent) => void;
  onEpisodeComplete?: (event: EpisodeCompleteEvent) => void;
  onMethodComplete?: (event: MethodCompleteEvent) => void;
  onComparisonComplete?: (event: ComparisonCompleteEvent) => void;
  onError?: (event: ErrorEvent) => void;
  onAnyEvent?: StreamEventHandler;
}

/**
 * JSS Streaming Client - Manages WebSocket connection and streaming operations
 */
export class JSSStreamingClient {
  private ws: WebSocket | null = null;
  private clientId: string | null = null;
  private isConnected: boolean = false;
  private subscriptions: Set<string> = new Set();
  private handlers: StreamEventHandlers = {};
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectInterval: number = 1000;

  constructor(
    private baseUrl: string = 'ws://localhost:8081/api/v1/stream/ws'
  ) {}

  /**
   * Connect to the streaming WebSocket
   */
  async connect(): Promise<boolean> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.baseUrl);

        this.ws.onopen = () => {
          this.isConnected = true;
          this.reconnectAttempts = 0;
          console.log('🔌 Connected to JSS streaming server');
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
            
            if (message.type === 'connection_established') {
              this.clientId = message.client_id;
              resolve(true);
            }
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = () => {
          this.isConnected = false;
          console.log('🔌 Disconnected from streaming server');
          this.handleReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        // Timeout for connection
        setTimeout(() => {
          if (!this.isConnected) {
            reject(new Error('Connection timeout'));
          }
        }, 5000);

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Disconnect from the streaming WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
    this.clientId = null;
    this.subscriptions.clear();
  }

  /**
   * Set event handlers
   */
  setEventHandlers(handlers: StreamEventHandlers): void {
    this.handlers = { ...this.handlers, ...handlers };
  }

  /**
   * Start a streaming comparison
   */
  async startStreamingComparison(request: StreamComparisonRequest): Promise<string> {
    const response = await handleDirectApiCall(() =>
      axiosInstance.post<{ session_id: string }>('/stream/start', request)
    );

    if (!response?.session_id) {
      throw new Error('Failed to start streaming comparison');
    }

    // Auto-subscribe to the session
    await this.subscribeToSession(response.session_id);
    
    return response.session_id;
  }

  /**
   * Subscribe to a streaming session
   */
  async subscribeToSession(sessionId: string): Promise<void> {
    if (!this.isConnected || !this.ws) {
      throw new Error('Not connected to streaming server');
    }

    const message = {
      type: 'subscribe',
      session_id: sessionId
    };

    this.ws.send(JSON.stringify(message));
    this.subscriptions.add(sessionId);
  }

  /**
   * Unsubscribe from a streaming session
   */
  async unsubscribeFromSession(sessionId: string): Promise<void> {
    if (!this.isConnected || !this.ws) return;

    const message = {
      type: 'unsubscribe',
      session_id: sessionId
    };

    this.ws.send(JSON.stringify(message));
    this.subscriptions.delete(sessionId);
  }

  /**
   * Get session information
   */
  async getSessionInfo(sessionId: string): Promise<StreamSessionInfo | null> {
    return handleDirectApiCall(() =>
      axiosInstance.get<StreamSessionInfo>(`/stream/sessions/${sessionId}`)
    );
  }

  /**
   * Get all sessions
   */
  async getAllSessions(): Promise<StreamSessionInfo[]> {
    const response = await handleDirectApiCall(() =>
      axiosInstance.get<StreamSessionInfo[]>('/stream/sessions')
    );
    return response || [];
  }

  /**
   * Cancel a streaming session
   */
  async cancelSession(sessionId: string): Promise<void> {
    await handleDirectApiCall(() =>
      axiosInstance.post(`/stream/sessions/${sessionId}/cancel`)
    );
  }

  /**
   * Check if connected
   */
  getConnectionStatus(): boolean {
    return this.isConnected;
  }

  /**
   * Get client ID
   */
  getClientId(): string | null {
    return this.clientId;
  }

  /**
   * Handle incoming WebSocket messages
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private handleMessage(message: any): void {
    const event = message as StreamEvent;

    // Call specific handler
    switch (event.type) {
      case StreamEventType.CONNECTION_ESTABLISHED:
        this.handlers.onConnection?.(event as ConnectionEstablishedEvent);
        break;
      case StreamEventType.SESSION_CREATED:
        this.handlers.onSessionCreated?.(event as SessionCreatedEvent);
        break;
      case StreamEventType.COMPARISON_START:
        this.handlers.onComparisonStart?.(event as ComparisonStartEvent);
        break;
      case StreamEventType.EPISODE_PROGRESS:
        this.handlers.onEpisodeProgress?.(event as EpisodeProgressEvent);
        break;
      case StreamEventType.EPISODE_COMPLETE:
        this.handlers.onEpisodeComplete?.(event as EpisodeCompleteEvent);
        break;
      case StreamEventType.METHOD_COMPLETE:
        this.handlers.onMethodComplete?.(event as MethodCompleteEvent);
        break;
      case StreamEventType.COMPARISON_COMPLETE:
        this.handlers.onComparisonComplete?.(event as ComparisonCompleteEvent);
        break;
      case StreamEventType.ERROR:
        this.handlers.onError?.(event as ErrorEvent);
        break;
    }

    // Call generic handler
    this.handlers.onAnyEvent?.(event);
  }

  /**
   * Handle reconnection logic
   */
  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect().catch(console.error);
      }, this.reconnectInterval * this.reconnectAttempts);
    }
  }
}

/**
 * REST API endpoints for streaming management
 */
export const streamingAPI = {
  /**
   * Get streaming health status
   */
  getHealth: async () => {
    return handleDirectApiCall(() =>
      axiosInstance.get('/stream/health')
    );
  },

  /**
   * Get streaming statistics
   */
  getStats: async () => {
    return handleDirectApiCall(() =>
      axiosInstance.get('/stream/stats')
    );
  },

  /**
   * Cleanup streaming resources
   */
  cleanup: async () => {
    return handleDirectApiCall(() =>
      axiosInstance.post('/stream/cleanup')
    );
  },
};
