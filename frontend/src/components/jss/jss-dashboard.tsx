/**
 * JSS Dashboard Component - Main dashboard for JSS operations
 * Demonstrates proper JSS streaming API usage following frontend rules
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { jssAPI } from '@/apis/jss-api';
import { JSSStreamingClient } from '@/apis/streaming-api';
import { getErrorMessage } from '@/utils/apiHandler';
import { AgentType, DispatchingRule } from '@/types/jss.type';
import type {
  HealthResponse,
  InstanceInfo,
  ControllerInfo,
} from '@/types/jss.type';
import type {
  StreamComparisonRequest,
  StreamResults,
  ComparisonStartEvent,
  EpisodeProgressEvent,
  EpisodeCompleteEvent,
  MethodCompleteEvent,
  ComparisonCompleteEvent,
  ErrorEvent,
  StreamSessionInfo,
  ConnectionEstablishedEvent,
  SessionCreatedEvent,
  StreamMethodResult,
} from '@/apis/streaming-api';
import type { LoadingState } from '@/types/common.type';

interface JssDashboardProps {
  title: string;
  subtitle?: string;
}

function JssDashboard({ title, subtitle }: JssDashboardProps) {
  // State management
  const [loadingState, setLoadingState] = useState<LoadingState>('idle');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [instances, setInstances] = useState<InstanceInfo[]>([]);
  const [controllers, setControllers] = useState<ControllerInfo[]>([]);
  const [selectedInstance, setSelectedInstance] = useState<string>('');
  const [selectedController, setSelectedController] = useState<string>('');
  
  // Streaming-specific state
  const [streamingClient, setStreamingClient] = useState<JSSStreamingClient | null>(null);
  const [currentSession, setCurrentSession] = useState<StreamSessionInfo | null>(null);
  const [comparisonResults, setComparisonResults] = useState<StreamResults | null>(null);
  const [currentProgress, setCurrentProgress] = useState<number>(0);
  const [currentEpisode, setCurrentEpisode] = useState<number>(0);
  const [totalEpisodes, setTotalEpisodes] = useState<number>(0);
  const [currentMethod, setCurrentMethod] = useState<string>('');
  const [realtimeMetrics, setRealtimeMetrics] = useState<Record<string, {
    current_makespan?: number;
    total_reward?: number;
    episode?: number;
    step?: number;
    makespan?: number;
    execution_time?: number;
  }>>({});
  const [isConnected, setIsConnected] = useState<boolean>(false);
  
  const [error, setError] = useState<string | null>(null);

  // Refs for cleanup
  const clientRef = useRef<JSSStreamingClient | null>(null);  // Load initial data
  useEffect(() => {
    loadDashboardData();
    initializeStreamingClient();
    
    // Cleanup on unmount
    return () => {
      if (clientRef.current) {
        clientRef.current.disconnect();
      }
    };
  }, []);

  const initializeStreamingClient = useCallback(() => {
    try {
      const client = new JSSStreamingClient();
      clientRef.current = client;
      setStreamingClient(client);

      // Set up event handlers
      client.setEventHandlers({
        onConnection: (event: ConnectionEstablishedEvent) => {
          console.log('Streaming connection established:', event.client_id);
          setIsConnected(true);
        },

        onSessionCreated: (event: SessionCreatedEvent) => {
          console.log('Session created:', event.session);
          setCurrentSession(event.session);
        },

        onComparisonStart: (event: ComparisonStartEvent) => {
          console.log('Comparison started:', event);
          setTotalEpisodes(event.total_episodes_per_method * event.total_methods);
          setCurrentProgress(0);
          setCurrentEpisode(0);
          setCurrentMethod('');
          setLoadingState('loading');
        },

        onEpisodeProgress: (event: EpisodeProgressEvent) => {
          setCurrentEpisode(event.episode);
          setCurrentMethod(event.agent_name);
          
          // Update realtime metrics if available
          if (event.current_makespan) {
            setRealtimeMetrics(prev => ({
              ...prev,
              [event.agent_name]: {
                current_makespan: event.current_makespan,
                total_reward: event.total_reward,
                episode: event.episode,
                step: event.step,
              }
            }));
          }
        },

        onEpisodeComplete: (event: EpisodeCompleteEvent) => {
          console.log('Episode completed:', event);
          setCurrentProgress(prev => Math.min(prev + (100 / totalEpisodes), 100));
          
          // Update episode metrics
          setRealtimeMetrics(prev => ({
            ...prev,
            [event.agent_name]: {
              ...prev[event.agent_name],
              makespan: event.makespan,
              total_reward: event.total_reward,
              execution_time: event.execution_time,
            }
          }));
        },

        onMethodComplete: (event: MethodCompleteEvent) => {
          console.log('Method completed:', event);
          setCurrentProgress((event.completed_methods / event.total_methods) * 100);
        },

        onComparisonComplete: (event: ComparisonCompleteEvent) => {
          console.log('Comparison completed:', event);
          const results = event.results as Record<string, StreamMethodResult>;
          setComparisonResults({
            session_id: event.session_id,
            instance_name: selectedInstance,
            total_methods: Object.keys(results).length,
            results: results,
            best_method: Object.entries(results).reduce((best, [method, metrics]) => 
              !best || metrics.best_makespan < results[best].best_makespan ? method : best
            , ''),
            best_makespan: Math.min(...Object.values(results).map(r => r.best_makespan)),
          });
          setCurrentProgress(100);
          setLoadingState('succeeded');
        },

        onError: (event: ErrorEvent) => {
          console.error('Streaming error:', event);
          setError(`Streaming error: ${event.error_message}`);
          setLoadingState('failed');
        },
      });

      // Initialize connection
      client.connect().catch((err) => {
        console.error('Failed to connect streaming client:', err);
        setError('Failed to connect to streaming server');
        setIsConnected(false);
      });    } catch (err) {
      console.error('Failed to initialize streaming client:', err);
      setError('Failed to initialize streaming connection');
    }
  }, []);

  const loadDashboardData = async () => {
    setLoadingState('loading');
    setError(null);

    try {
      // Load health status, instances, and controllers in parallel
      const [healthData, instancesData, controllersData] = await Promise.all([
        jssAPI.getHealth(),
        jssAPI.getInstances(true), // Include stats
        jssAPI.getControllers(true), // Include stats
      ]);

      setHealth(healthData);
      setInstances(instancesData || []);
      setControllers(controllersData || []);
      
      // Auto-select first instance if available
      if (instancesData && instancesData.length > 0) {
        setSelectedInstance(instancesData[0].name);
      }

      setLoadingState('succeeded');
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      setLoadingState('failed');
      console.error('Failed to load dashboard data:', errorMessage);
    }
  };

  const runStreamingComparison = async () => {
    if (!selectedInstance) {
      setError('Please select an instance');
      return;
    }

    if (!streamingClient) {
      setError('Streaming client not initialized');
      return;
    }

    if (!isConnected) {
      setError('Not connected to streaming server');
      return;
    }

    setLoadingState('loading');
    setError(null);
    setComparisonResults(null);
    setCurrentProgress(0);
    setCurrentEpisode(0);
    setCurrentMethod('');
    setRealtimeMetrics({});

    try {
      const request: StreamComparisonRequest = {
        instance_name: selectedInstance,
        controller_name: selectedController || undefined,
        agents: [AgentType.HYBRID, AgentType.LOOKAHEAD],
        dispatching_rules: [DispatchingRule.SPT, DispatchingRule.FIFO],
        num_episodes: 10,
        include_random_baseline: true,
      };

      const sessionId = await streamingClient.startStreamingComparison(request);
      console.log('Started streaming comparison with session ID:', sessionId);
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      setLoadingState('failed');
      console.error('Streaming comparison failed:', errorMessage);
    }
  };

  const refreshInstances = async () => {
    try {
      const instancesData = await jssAPI.getInstances(true);
      setInstances(instancesData || []);
    } catch (err) {
      console.error('Failed to refresh instances:', getErrorMessage(err));
    }
  };

  return (
    <div className="min-h-screen bg-[color:var(--background)] text-[color:var(--foreground)] p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">{title}</h1>
        {subtitle && (
          <p className="text-[color:var(--muted-foreground)]">{subtitle}</p>
        )}
      </div>

      {/* Streaming Connection Status */}
      <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-4 mb-6">
        <h2 className="text-xl font-semibold mb-2">Streaming Connection</h2>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className={isConnected ? 'text-green-600' : 'text-red-600'}>
            {isConnected ? 'Connected to streaming server' : 'Disconnected from streaming server'}
          </span>
          {currentSession && (
            <span className="text-sm text-[color:var(--muted-foreground)] ml-4">
              Session: {currentSession.session_id}
            </span>
          )}
        </div>
      </div>

      {/* Health Status */}
      {health && (
        <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-4 mb-6">
          <h2 className="text-xl font-semibold mb-2">System Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <span className="text-sm text-[color:var(--muted-foreground)]">Status:</span>
              <p className="font-medium text-green-600">{health.status}</p>
            </div>
            <div>
              <span className="text-sm text-[color:var(--muted-foreground)]">Instances:</span>
              <p className="font-medium">{health.available_instances || 0}</p>
            </div>
            <div>
              <span className="text-sm text-[color:var(--muted-foreground)]">Controllers:</span>
              <p className="font-medium">{health.available_controllers || 0}</p>
            </div>
          </div>
        </div>
      )}

      {/* Progress Indicator */}
      {loadingState === 'loading' && (
        <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-4 mb-6">
          <h2 className="text-xl font-semibold mb-2">Real-time Progress</h2>
          <div className="space-y-3">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${currentProgress}%` }}
              ></div>
            </div>
            <div className="text-sm text-[color:var(--muted-foreground)] flex justify-between">
              <span>Progress: {currentProgress.toFixed(1)}%</span>
              <span>Episode: {currentEpisode}/{totalEpisodes}</span>
            </div>
            {currentMethod && (
              <div className="text-sm">
                <span className="font-medium">Current Method:</span> {currentMethod}
              </div>
            )}
            
            {/* Real-time metrics */}
            {Object.keys(realtimeMetrics).length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-medium mb-2">Real-time Metrics:</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                  {Object.entries(realtimeMetrics).map(([method, metrics]) => (
                    <div key={method} className="bg-[color:var(--muted)] p-2 rounded">
                      <div className="font-medium">{method}</div>
                      {metrics.current_makespan && (
                        <div>Makespan: {metrics.current_makespan.toFixed(2)}</div>
                      )}
                      {metrics.total_reward && (
                        <div>Reward: {metrics.total_reward.toFixed(2)}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6">
          <p className="font-medium">Error:</p>
          <p>{error}</p>
        </div>
      )}

      {/* Configuration Panel */}
      <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Streaming Comparison Configuration</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {/* Instance Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">
              JSS Instance *
            </label>
            <select
              value={selectedInstance}
              onChange={(e) => setSelectedInstance(e.target.value)}
              className="w-full p-2 border border-[color:var(--border)] rounded-md bg-[color:var(--background)]"
              disabled={loadingState === 'loading'}
            >
              <option value="">Select an instance...</option>
              {instances.map((instance) => (
                <option key={instance.name} value={instance.name}>
                  {instance.name} ({instance.size})
                </option>
              ))}
            </select>
          </div>

          {/* Controller Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Controller (Optional)
            </label>
            <select
              value={selectedController}
              onChange={(e) => setSelectedController(e.target.value)}
              className="w-full p-2 border border-[color:var(--border)] rounded-md bg-[color:var(--background)]"
              disabled={loadingState === 'loading'}
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

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={runStreamingComparison}
            disabled={loadingState === 'loading' || !selectedInstance || !isConnected}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loadingState === 'loading' ? '🔄 Streaming...' : '🌊 Start Streaming Comparison'}
          </button>
          
          <button
            onClick={refreshInstances}
            disabled={loadingState === 'loading'}
            className="px-6 py-2 bg-[color:var(--muted)] text-[color:var(--muted-foreground)] rounded-md hover:bg-[color:var(--accent)]"
          >
            Refresh Data
          </button>
        </div>
      </div>

      {/* Results Display */}
      {comparisonResults && (
        <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Streaming Comparison Results</h2>
          
          <div className="mb-4">
            <p><strong>Instance:</strong> {comparisonResults.instance_name}</p>
            <p><strong>Session ID:</strong> {comparisonResults.session_id}</p>
            {comparisonResults.best_method && (
              <>
                <p><strong>Best Method:</strong> {comparisonResults.best_method}</p>
                <p><strong>Best Makespan:</strong> {comparisonResults.best_makespan?.toFixed(2)}</p>
              </>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-[color:var(--border)]">
              <thead>
                <tr className="bg-[color:var(--muted)]">
                  <th className="border border-[color:var(--border)] p-2 text-left">Method</th>
                  <th className="border border-[color:var(--border)] p-2 text-left">Avg Makespan</th>
                  <th className="border border-[color:var(--border)] p-2 text-left">Best Makespan</th>
                  <th className="border border-[color:var(--border)] p-2 text-left">Episodes</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(comparisonResults.results).map(([method, metrics]) => (
                  <tr key={method}>
                    <td className="border border-[color:var(--border)] p-2">{method}</td>
                    <td className="border border-[color:var(--border)] p-2">
                      {metrics.avg_makespan.toFixed(2)}
                    </td>
                    <td className="border border-[color:var(--border)] p-2">
                      {metrics.best_makespan.toFixed(2)}
                    </td>
                    <td className="border border-[color:var(--border)] p-2">
                      {metrics.episodes_completed}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default JssDashboard;
