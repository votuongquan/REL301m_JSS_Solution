/**
 * JSS Visualization Component
 * Demonstrates proper visualization generation with JSS API
 */

'use client';

import { useState, useEffect } from 'react';
import { jssAPI } from '@/apis/jss-api';
import { getErrorMessage } from '@/utils/apiHandler';
import type {
  VisualizationRequest,
  VisualizationResponse,
  BackgroundTaskStatus,
  InstanceInfo,
} from '@/types/jss.type';

interface JssVisualizationProps {
  title: string;
}

function JssVisualization({ title }: JssVisualizationProps) {
  // State management
  const [instances, setInstances] = useState<InstanceInfo[]>([]);
  const [recentTasks, setRecentTasks] = useState<BackgroundTaskStatus[]>([]);
  const [selectedInstance, setSelectedInstance] = useState<string>('');
  const [selectedResultId, setSelectedResultId] = useState<string>('');
  const [selectedTypes, setSelectedTypes] = useState<string[]>(['dashboard', 'detailed', 'gantt']);
  const [selectedFormat, setSelectedFormat] = useState<string>('png');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedPaths, setGeneratedPaths] = useState<string[]>([]);

  // Available visualization types
  const visualizationTypes = [
    { id: 'dashboard', label: 'Comprehensive Dashboard', description: 'Overview of all methods' },
    { id: 'detailed', label: 'Detailed Comparison', description: 'In-depth analysis charts' },
    { id: 'gantt', label: 'Gantt Charts', description: 'Schedule visualization' },
    { id: 'performance', label: 'Performance Metrics', description: 'Statistical analysis' },
    { id: 'timeline', label: 'Timeline View', description: 'Execution timeline' },
  ];

  // Available formats
  const formats = [
    { id: 'png', label: 'PNG Image', description: 'High-quality raster image' },
    { id: 'svg', label: 'SVG Vector', description: 'Scalable vector graphics' },
    { id: 'pdf', label: 'PDF Document', description: 'Printable document' },
    { id: 'html', label: 'HTML Interactive', description: 'Interactive web page' },
  ];

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [instancesData, tasksData] = await Promise.all([
        jssAPI.getInstances(false),
        jssAPI.getAllTasks(),
      ]);

      setInstances(instancesData || []);
      
      // Filter for completed tasks that might have results
      const completedTasks = (tasksData || []).filter(
        task => task.status === 'completed' && task.result
      );
      setRecentTasks(completedTasks);

      if (instancesData && instancesData.length > 0) {
        setSelectedInstance(instancesData[0].name);
      }

      if (completedTasks.length > 0) {
        setSelectedResultId(completedTasks[0].task_id);
      }
    } catch (err) {
      setError(`Failed to load data: ${getErrorMessage(err)}`);
    }
  };

  const generateVisualizations = async () => {
    if (!selectedInstance || !selectedResultId) {
      setError('Please select an instance and result ID');
      return;
    }

    if (selectedTypes.length === 0) {
      setError('Please select at least one visualization type');
      return;
    }

    setLoading(true);
    setError(null);
    setGeneratedPaths([]);

    try {
      const request: VisualizationRequest = {
        instance_name: selectedInstance,
        results_id: selectedResultId,
        visualization_types: selectedTypes,
        format: selectedFormat,
      };

      const response = await jssAPI.generateVisualizations(request);
      
      if (response?.visualization_paths) {
        setGeneratedPaths(response.visualization_paths);
      }
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(`Failed to generate visualizations: ${errorMessage}`);
      console.error('Visualization generation failed:', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const toggleVisualizationType = (typeId: string) => {
    setSelectedTypes(prev => 
      prev.includes(typeId)
        ? prev.filter(id => id !== typeId)
        : [...prev, typeId]
    );
  };

  const downloadVisualization = async (filePath: string) => {
    try {
      const blob = await jssAPI.downloadFile(filePath);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filePath.split('/').pop() || 'visualization';
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download visualization:', getErrorMessage(err));
    }
  };

  const refreshData = async () => {
    await loadInitialData();
  };

  return (
    <div className="bg-[color:var(--background)] text-[color:var(--foreground)] p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">{title}</h1>
        <p className="text-[color:var(--muted-foreground)]">
          Generate and download visualizations from JSS comparison results
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6">
          <p>{error}</p>
        </div>
      )}

      {/* Configuration Panel */}
      <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Visualization Configuration</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Instance and Result Selection */}
          <div className="space-y-4">
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
                Comparison Result *
              </label>
              <select
                value={selectedResultId}
                onChange={(e) => setSelectedResultId(e.target.value)}
                className="w-full p-2 border border-[color:var(--border)] rounded-md bg-[color:var(--background)]"
                disabled={loading}
              >
                <option value="">Select a result...</option>
                {recentTasks.map((task) => (
                  <option key={task.task_id} value={task.task_id}>
                    {task.task_id} ({new Date(task.created_at).toLocaleDateString()})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Output Format
              </label>
              <select
                value={selectedFormat}
                onChange={(e) => setSelectedFormat(e.target.value)}
                className="w-full p-2 border border-[color:var(--border)] rounded-md bg-[color:var(--background)]"
                disabled={loading}
              >
                {formats.map((format) => (
                  <option key={format.id} value={format.id}>
                    {format.label} - {format.description}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Visualization Types */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Visualization Types *
            </label>
            <div className="space-y-2">
              {visualizationTypes.map((type) => (
                <label
                  key={type.id}
                  className="flex items-start gap-3 p-3 border border-[color:var(--border)] rounded-lg hover:bg-[color:var(--muted)] cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedTypes.includes(type.id)}
                    onChange={() => toggleVisualizationType(type.id)}
                    className="mt-1"
                    disabled={loading}
                  />
                  <div className="flex-1">
                    <div className="font-medium">{type.label}</div>
                    <div className="text-sm text-[color:var(--muted-foreground)]">
                      {type.description}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 mt-6">
          <button
            onClick={generateVisualizations}
            disabled={loading || !selectedInstance || !selectedResultId || selectedTypes.length === 0}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Generating...' : 'Generate Visualizations'}
          </button>

          <button
            onClick={refreshData}
            disabled={loading}
            className="px-6 py-2 bg-[color:var(--muted)] text-[color:var(--muted-foreground)] rounded-md hover:bg-[color:var(--accent)]"
          >
            Refresh Data
          </button>
        </div>
      </div>

      {/* Generated Visualizations */}
      {generatedPaths.length > 0 && (
        <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Generated Visualizations</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {generatedPaths.map((path) => (
              <div
                key={path}
                className="border border-[color:var(--border)] rounded-lg p-4 hover:bg-[color:var(--muted)] transition-colors"
              >
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-2xl">🖼️</span>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate" title={path}>
                      {path.split('/').pop()}
                    </div>
                    <div className="text-sm text-[color:var(--muted-foreground)] truncate">
                      {path}
                    </div>
                  </div>
                </div>
                
                <button
                  onClick={() => downloadVisualization(path)}
                  className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  ⬇️ Download
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Loading Indicator */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-[color:var(--card)] rounded-lg p-6">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-center">Generating visualizations...</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default JssVisualization;
