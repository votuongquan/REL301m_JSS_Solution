/**
 * Background Task Manager Component
 * Demonstrates proper background task handling with JSS API
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { jssAPI } from '@/apis/jss-api';
import { getErrorMessage } from '@/utils/apiHandler';
import { AgentType, DispatchingRule, TaskStatus } from '@/types/jss.type';
import type {
  ComparisonRequest,
  BackgroundTaskStatus,
  BackgroundTaskResponse,
  InstanceInfo,
  ControllerInfo,
} from '@/types/jss.type';

interface BackgroundTaskManagerProps {
  title: string;
}

function BackgroundTaskManager({ title }: BackgroundTaskManagerProps) {
  // State management
  const [instances, setInstances] = useState<InstanceInfo[]>([]);
  const [controllers, setControllers] = useState<ControllerInfo[]>([]);
  const [activeTasks, setActiveTasks] = useState<BackgroundTaskStatus[]>([]);
  const [selectedInstance, setSelectedInstance] = useState<string>('');
  const [selectedController, setSelectedController] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Polling intervals
  const pollingIntervals = new Map<string, NodeJS.Timeout>();

  // Load initial data
  useEffect(() => {
    loadInitialData();
    loadAllTasks();
  }, []);

  // Cleanup polling intervals on unmount
  useEffect(() => {
    return () => {
      pollingIntervals.forEach((interval) => clearInterval(interval));
    };
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
  };

  const loadAllTasks = async () => {
    try {
      const tasks = await jssAPI.getAllTasks();
      setActiveTasks(tasks || []);

      // Start polling for running tasks
      tasks?.forEach((task) => {
        if (task.status === TaskStatus.RUNNING || task.status === TaskStatus.PENDING) {
          startTaskPolling(task.task_id);
        }
      });
    } catch (err) {
      console.error('Failed to load tasks:', getErrorMessage(err));
    }
  };

  const startBackgroundComparison = async () => {
    if (!selectedInstance) {
      setError('Please select an instance');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const request: ComparisonRequest = {
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
        include_visualizations: true,
      };

      const response = await jssAPI.runComparisonBackground(request);
      
      if (response?.task_id) {
        // Add new task to the list
        const newTask: BackgroundTaskStatus = {
          task_id: response.task_id,
          status: TaskStatus.PENDING,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };

        setActiveTasks((prev) => [newTask, ...prev]);
        startTaskPolling(response.task_id);
      }

      setLoading(false);
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(`Failed to start comparison: ${errorMessage}`);
      setLoading(false);
    }
  };

  const startTaskPolling = useCallback((taskId: string) => {
    // Clear existing interval if any
    const existingInterval = pollingIntervals.get(taskId);
    if (existingInterval) {
      clearInterval(existingInterval);
    }

    // Start new polling interval
    const interval = setInterval(async () => {
      try {
        const taskStatus = await jssAPI.getTaskStatus(taskId);
        
        if (taskStatus) {
          // Update task in the list
          setActiveTasks((prev) =>
            prev.map((task) =>
              task.task_id === taskId ? taskStatus : task
            )
          );

          // Stop polling if task is completed or failed
          if (
            taskStatus.status === TaskStatus.COMPLETED ||
            taskStatus.status === TaskStatus.FAILED
          ) {
            clearInterval(interval);
            pollingIntervals.delete(taskId);
          }
        }
      } catch (err) {
        console.error(`Polling failed for task ${taskId}:`, getErrorMessage(err));
        clearInterval(interval);
        pollingIntervals.delete(taskId);
      }
    }, 3000); // Poll every 3 seconds

    pollingIntervals.set(taskId, interval);
  }, []);

  const refreshTasks = async () => {
    await loadAllTasks();
  };

  const getStatusColor = (status: TaskStatus): string => {
    switch (status) {
      case TaskStatus.PENDING:
        return 'text-yellow-600';
      case TaskStatus.RUNNING:
        return 'text-blue-600';
      case TaskStatus.COMPLETED:
        return 'text-green-600';
      case TaskStatus.FAILED:
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: TaskStatus): string => {
    switch (status) {
      case TaskStatus.PENDING:
        return '⏳';
      case TaskStatus.RUNNING:
        return '🔄';
      case TaskStatus.COMPLETED:
        return '✅';
      case TaskStatus.FAILED:
        return '❌';
      default:
        return '❓';
    }
  };

  return (
    <div className="bg-[color:var(--background)] text-[color:var(--foreground)] p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">{title}</h1>
        <p className="text-[color:var(--muted-foreground)]">
          Run JSS comparisons in the background and monitor their progress
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6">
          <p>{error}</p>
        </div>
      )}

      {/* Start New Comparison */}
      <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Start New Background Comparison</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              JSS Instance *
            </label>
            <select
              value={selectedInstance}
              onChange={(e) => setSelectedInstance(e.target.value)}
              className="w-full p-2 border border-[color:var(--border)] rounded-md bg-[color:var(--background)]"
              disabled={loading}
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
              disabled={loading}
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
            disabled={loading || !selectedInstance}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Starting...' : 'Start Background Comparison'}
          </button>

          <button
            onClick={refreshTasks}
            className="px-6 py-2 bg-[color:var(--muted)] text-[color:var(--muted-foreground)] rounded-md hover:bg-[color:var(--accent)]"
          >
            Refresh Tasks
          </button>
        </div>
      </div>

      {/* Active Tasks */}
      <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Background Tasks</h2>
        
        {activeTasks.length === 0 ? (
          <p className="text-[color:var(--muted-foreground)]">No background tasks</p>
        ) : (
          <div className="space-y-4">
            {activeTasks.map((task) => (
              <div
                key={task.task_id}
                className="border border-[color:var(--border)] rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{getStatusIcon(task.status)}</span>
                    <span className={`font-medium ${getStatusColor(task.status)}`}>
                      {task.status.toUpperCase()}
                    </span>
                    <span className="text-sm text-[color:var(--muted-foreground)]">
                      ID: {task.task_id}
                    </span>
                  </div>
                  <div className="text-sm text-[color:var(--muted-foreground)]">
                    Created: {new Date(task.created_at).toLocaleString()}
                  </div>
                </div>

                {task.progress !== undefined && (
                  <div className="mb-2">
                    <div className="flex justify-between text-sm mb-1">
                      <span>Progress</span>
                      <span>{task.progress.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${task.progress}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                {task.error && (
                  <div className="text-red-600 text-sm bg-red-50 p-2 rounded">
                    <strong>Error:</strong> {task.error}
                  </div>
                )}

                {task.result && task.status === TaskStatus.COMPLETED && (
                  <div className="text-green-600 text-sm bg-green-50 p-2 rounded">
                    <strong>Completed:</strong> Task finished successfully
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
