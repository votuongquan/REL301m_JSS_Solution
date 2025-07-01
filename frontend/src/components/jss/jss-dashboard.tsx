/**
 * JSS Dashboard Component - Main dashboard for JSS operations
 * Demonstrates proper JSS API usage following frontend rules
 */

'use client';

import { useState, useEffect } from 'react';
import { jssAPI } from '@/apis/jss-api';
import { getErrorMessage } from '@/utils/apiHandler';
import { AgentType, DispatchingRule } from '@/types/jss.type';
import type {
  HealthResponse,
  InstanceInfo,
  ControllerInfo,
  ComparisonRequest,
  ComparisonResult,
} from '@/types/jss.type';
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
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load initial data
  useEffect(() => {
    loadDashboardData();
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

  const runComparison = async () => {
    if (!selectedInstance) {
      setError('Please select an instance');
      return;
    }

    setLoadingState('loading');
    setError(null);

    try {
      const request: ComparisonRequest = {
        instance_name: selectedInstance,
        controller_name: selectedController || undefined,
        agents: [AgentType.HYBRID, AgentType.LOOKAHEAD],
        dispatching_rules: [DispatchingRule.SPT, DispatchingRule.FIFO],
        num_episodes: 10,
        include_random_baseline: true,
        include_visualizations: true,
      };

      const result = await jssAPI.runComparison(request);
      setComparisonResult(result);
      setLoadingState('succeeded');
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      setLoadingState('failed');
      console.error('Comparison failed:', errorMessage);
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

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6">
          <p className="font-medium">Error:</p>
          <p>{error}</p>
        </div>
      )}

      {/* Configuration Panel */}
      <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Comparison Configuration</h2>
        
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
            onClick={runComparison}
            disabled={loadingState === 'loading' || !selectedInstance}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loadingState === 'loading' ? 'Running...' : 'Run Comparison'}
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
      {comparisonResult && (
        <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Comparison Results</h2>
          
          <div className="mb-4">
            <p><strong>Instance:</strong> {comparisonResult.instance_name}</p>
            {comparisonResult.controller_name && (
              <p><strong>Controller:</strong> {comparisonResult.controller_name}</p>
            )}
            <p><strong>Best Method:</strong> {comparisonResult.best_method}</p>
            <p><strong>Best Makespan:</strong> {comparisonResult.best_makespan.toFixed(2)}</p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-[color:var(--border)]">
              <thead>
                <tr className="bg-[color:var(--muted)]">
                  <th className="border border-[color:var(--border)] p-2 text-left">Method</th>
                  <th className="border border-[color:var(--border)] p-2 text-left">Avg Makespan</th>
                  <th className="border border-[color:var(--border)] p-2 text-left">Std Dev</th>
                  <th className="border border-[color:var(--border)] p-2 text-left">Episodes</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(comparisonResult.results).map(([method, metrics]) => (
                  <tr key={method}>
                    <td className="border border-[color:var(--border)] p-2">{method}</td>
                    <td className="border border-[color:var(--border)] p-2">
                      {metrics.avg_makespan.toFixed(2)}
                    </td>
                    <td className="border border-[color:var(--border)] p-2">
                      {metrics.std_makespan.toFixed(2)}
                    </td>
                    <td className="border border-[color:var(--border)] p-2">
                      {metrics.total_episodes}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Loading Indicator */}
      {loadingState === 'loading' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-[color:var(--card)] rounded-lg p-6">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-center">Processing...</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default JssDashboard;
