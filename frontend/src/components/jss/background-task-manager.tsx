/**
 * Background Task Manager Component
 * Demonstrates proper streaming session management with JSS Streaming API
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { jssAPI } from '@/apis/jss-api';
import { JSSStreamingClient } from '@/apis/streaming-api';
import { getErrorMessage } from '@/utils/apiHandler';
import { AgentType, DispatchingRule } from '@/types/jss.type';
import type {
  InstanceInfo,
  ControllerInfo,
} from '@/types/jss.type';
import type {
  StreamComparisonRequest,
  StreamSessionInfo,
  StreamResults,
  ConnectionEstablishedEvent,
  SessionCreatedEvent,
  ComparisonStartEvent,
  EpisodeProgressEvent,
  EpisodeCompleteEvent,
  MethodCompleteEvent,
  ComparisonCompleteEvent,
  ErrorEvent,
} from '@/apis/streaming-api';
import { StreamStatus } from '@/apis/streaming-api';

interface BackgroundTaskManagerProps {
  title: string;
}

function BackgroundTaskManager({ title }: BackgroundTaskManagerProps) {
  // State management
  const [instances, setInstances] = useState<InstanceInfo[]>([]);
  const [controllers, setControllers] = useState<ControllerInfo[]>([]);
  const [activeSessions, setActiveSessions] = useState<StreamSessionInfo[]>([]);
  const [selectedInstance, setSelectedInstance] = useState<string>('');
  const [selectedController, setSelectedController] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Streaming client
  const [streamingClient, setStreamingClient] = useState<JSSStreamingClient | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const clientRef = useRef<JSSStreamingClient | null>(null);

  // Session results tracking
  const [sessionResults, setSessionResults] = useState<Record<string, StreamResults>>({});  // Load initial data
  useEffect(() => {
    loadInitialData();
    initializeStreamingClient();
      // Cleanup on unmount
    return () => {
      if (clientRef.current) {
        clientRef.current.disconnect();
      }    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const initializeStreamingClient = useCallback(() => {
    try {
      const client = new JSSStreamingClient();
      clientRef.current = client;
      setStreamingClient(client);

      // Set up event handlers
      client.setEventHandlers({
        onConnection: (event: ConnectionEstablishedEvent) => {
          console.log('Background task manager connected:', event.client_id);
          setIsConnected(true);
          loadActiveSessions();
        },

        onSessionCreated: (event: SessionCreatedEvent) => {
          console.log('New session created:', event.session);
          setActiveSessions(prev => [event.session, ...prev]);
        },

        onComparisonStart: (event: ComparisonStartEvent) => {
          console.log('Comparison started for session:', event.session_id);
          updateSessionProgress(event.session_id, { 
            status: StreamStatus.RUNNING,
            progress: 0 
          });
        },

        onEpisodeProgress: (event: EpisodeProgressEvent) => {
          // Update progress for the session
          updateSessionProgress(event.session_id, {
            current_episode: event.episode,
            progress: calculateProgress(event)
          });
        },

        onEpisodeComplete: (event: EpisodeCompleteEvent) => {
          console.log(`Episode ${event.episode} completed for session ${event.session_id}`);
        },

        onMethodComplete: (event: MethodCompleteEvent) => {
          console.log(`Method ${event.method_name} completed for session ${event.session_id}`);
        },

        onComparisonComplete: (event: ComparisonCompleteEvent) => {
          console.log('Comparison completed for session:', event.session_id);
          updateSessionProgress(event.session_id, { 
            status: StreamStatus.COMPLETED,
            progress: 1.0 
          });
          
          // Store results
          setSessionResults(prev => ({
            ...prev,
            [event.session_id]: {
              session_id: event.session_id,
              instance_name: '',
              total_methods: Object.keys(event.results).length,
              results: event.results
            }
          }));
        },

        onError: (event: ErrorEvent) => {
          console.error('Streaming error:', event.error_message);
          if (event.session_id) {
            updateSessionProgress(event.session_id, { 
              status: StreamStatus.FAILED,
              error_message: event.error_message 
            });
          }
        }
      });

      // Connect to WebSocket
      client.connect();    } catch (err) {
      console.error('Failed to initialize streaming client:', err);
      setError(`Failed to initialize streaming: ${getErrorMessage(err)}`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadInitialData = async () => {
    try {
      const [instancesData, controllersData] = await Promise.all([
        jssAPI.getInstances(false),
        jssAPI.getControllers(false),
      ]);

      setInstances(instancesData || []);
      setControllers(controllersData || []);

      if (instancesData && instancesData.length > 0) {
        setSelectedInstance(instancesData[0].name);
      }
    } catch (err) {
      setError(`Failed to load data: ${getErrorMessage(err)}`);
    }
  };  const loadActiveSessions = async () => {
    try {
      if (!streamingClient) return;
      
      const sessions = await streamingClient.getAllSessions();
      setActiveSessions(sessions);
    } catch (err) {
      console.error('Failed to load active sessions:', getErrorMessage(err));
    }
  };

  const calculateProgress = (event: EpisodeProgressEvent): number => {
    // Basic progress calculation based on episode and step
    // This is a simplified version - you might want more sophisticated calculation
    return Math.min(0.9, event.episode * 0.1 + (event.step / 1000) * 0.05);
  };

  const updateSessionProgress = (sessionId: string, updates: Partial<StreamSessionInfo>) => {
    setActiveSessions(prev =>
      prev.map(session =>
        session.session_id === sessionId 
          ? { ...session, ...updates }
          : session
      )
    );
  };

  const startBackgroundComparison = async () => {
    if (!selectedInstance) {
      setError('Please select an instance');
      return;
    }

    if (!streamingClient || !isConnected) {
      setError('Streaming client not connected');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const request: StreamComparisonRequest = {
        instance_name: selectedInstance,
        controller_name: selectedController || undefined,
        agents: [AgentType.HYBRID, AgentType.LOOKAHEAD, AgentType.CONTROLLER],
        dispatching_rules: [
          DispatchingRule.SPT,
          DispatchingRule.FIFO,
          DispatchingRule.MWR,
          DispatchingRule.LWR,
        ],
        num_episodes: 20, // More episodes for comprehensive comparison
        include_random_baseline: true,
      };

      const sessionId = await streamingClient.startStreamingComparison(request);
      console.log('Started background comparison with session ID:', sessionId);

    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(`Failed to start comparison: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const refreshSessions = async () => {
    await loadActiveSessions();
  };

  const getStatusColor = (status: StreamStatus): string => {
    switch (status) {
      case StreamStatus.INITIALIZING:
        return 'text-yellow-600';
      case StreamStatus.RUNNING:
        return 'text-blue-600';
      case StreamStatus.COMPLETED:
        return 'text-green-600';
      case StreamStatus.FAILED:
        return 'text-red-600';
      case StreamStatus.CANCELLED:
        return 'text-gray-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: StreamStatus): string => {
    switch (status) {
      case StreamStatus.INITIALIZING:
        return '⏳';
      case StreamStatus.RUNNING:
        return '🔄';
      case StreamStatus.COMPLETED:
        return '✅';
      case StreamStatus.FAILED:
        return '❌';
      case StreamStatus.CANCELLED:
        return '🛑';
      default:
        return '❓';
    }
  };

  const subscribeToSession = async (sessionId: string) => {
    if (streamingClient && isConnected) {
      try {
        await streamingClient.subscribeToSession(sessionId);
        console.log('Subscribed to session:', sessionId);
      } catch (err) {
        console.error('Failed to subscribe to session:', err);
      }
    }
  };
  return (
    <div className="bg-[color:var(--background)] text-[color:var(--foreground)] p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">{title}</h1>
        <p className="text-[color:var(--muted-foreground)]">
          Run JSS comparisons as streaming sessions and monitor their real-time progress
        </p>
      </div>

      {/* Connection Status */}
      <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-4 mb-6">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="font-medium">
            Streaming: {isConnected ? 'Connected' : 'Disconnected'}
          </span>
          {isConnected && (
            <span className="text-sm text-[color:var(--muted-foreground)]">
              Real-time updates enabled
            </span>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6">
          <p>{error}</p>
        </div>
      )}

      {/* Start New Comparison */}
      <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Start New Streaming Comparison</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              JSS Instance *
            </label>
            <select
              value={selectedInstance}
              onChange={(e) => setSelectedInstance(e.target.value)}
              className="w-full p-2 border border-[color:var(--border)] rounded-md bg-[color:var(--background)]"
              disabled={loading || !isConnected}
            >
              <option value="">Select an instance...</option>
              {instances.map((instance) => (
                <option key={instance.name} value={instance.name}>
                  {instance.name} ({instance.size})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Controller (Optional)
            </label>
            <select
              value={selectedController}
              onChange={(e) => setSelectedController(e.target.value)}
              className="w-full p-2 border border-[color:var(--border)] rounded-md bg-[color:var(--background)]"
              disabled={loading || !isConnected}
            >
              <option value="">No controller</option>
              {controllers.map((controller) => (
                <option key={controller.name} value={controller.name}>
                  {controller.name} ({controller.num_people} people)
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex gap-4">
          <button
            onClick={startBackgroundComparison}
            disabled={loading || !selectedInstance || !isConnected}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Starting...' : 'Start Streaming Comparison'}
          </button>

          <button
            onClick={refreshSessions}
            disabled={!isConnected}
            className="px-6 py-2 bg-[color:var(--muted)] text-[color:var(--muted-foreground)] rounded-md hover:bg-[color:var(--accent)]"
          >
            Refresh Sessions
          </button>
        </div>
      </div>

      {/* Active Sessions */}
      <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Active Streaming Sessions</h2>
        
        {activeSessions.length === 0 ? (
          <p className="text-[color:var(--muted-foreground)]">No active streaming sessions</p>
        ) : (
          <div className="space-y-4">
            {activeSessions.map((session) => (
              <div
                key={session.session_id}
                className="border border-[color:var(--border)] rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className="text-lg">{getStatusIcon(session.status)}</span>
                    <span className={`font-medium ${getStatusColor(session.status)}`}>
                      {session.status.toUpperCase()}
                    </span>
                    <span className="text-sm text-[color:var(--muted-foreground)]">
                      ID: {session.session_id}
                    </span>
                  </div>
                  <div className="text-sm text-[color:var(--muted-foreground)]">
                    Created: {new Date(session.created_at).toLocaleString()}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                  <div>
                    <span className="text-sm text-[color:var(--muted-foreground)]">Instance:</span>
                    <p className="font-medium">{session.request_data.instance_name}</p>
                  </div>
                  <div>
                    <span className="text-sm text-[color:var(--muted-foreground)]">Episodes:</span>
                    <p className="font-medium">{session.current_episode}/{session.total_episodes}</p>
                  </div>
                  <div>
                    <span className="text-sm text-[color:var(--muted-foreground)]">Subscribers:</span>
                    <p className="font-medium">{session.subscriber_count}</p>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mb-3">
                  <div className="flex justify-between text-sm mb-1">
                    <span>Progress</span>
                    <span>{(session.progress * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${session.progress * 100}%` }}
                    ></div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <button
                    onClick={() => subscribeToSession(session.session_id)}
                    disabled={!isConnected}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 text-sm"
                  >
                    🔔 Subscribe
                  </button>
                  
                  {sessionResults[session.session_id] && (
                    <span className="px-4 py-2 bg-blue-100 text-blue-800 rounded-md text-sm">
                      📊 Results Available
                    </span>
                  )}
                </div>

                {session.error_message && (
                  <div className="mt-3 text-red-600 text-sm bg-red-50 p-2 rounded">
                    <strong>Error:</strong> {session.error_message}
                  </div>
                )}

                {/* Show results if available */}
                {sessionResults[session.session_id] && session.status === StreamStatus.COMPLETED && (
                  <div className="mt-3 text-green-600 text-sm bg-green-50 p-2 rounded">
                    <strong>Completed:</strong> {Object.keys(sessionResults[session.session_id].results).length} methods compared
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default BackgroundTaskManager;
