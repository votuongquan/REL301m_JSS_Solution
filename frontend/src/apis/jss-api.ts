/**
 * JSS API - Main API endpoints for JSS operations
 * Following the frontend rules for API integration
 */

import axiosInstance from './axiosInstance';
import { handleDirectApiCall } from '@/utils/apiHandler';
import type {
  HealthResponse,
  InstanceInfo,
  ControllerInfo,
  ComparisonRequest,
  ComparisonResult,
  SingleRunRequest,
  SingleRunResult,
  VisualizationRequest,
  VisualizationResponse,
  BackgroundTaskStatus,
  BackgroundTaskResponse,
  FileListResponse,
} from '@/types/jss.type';

/**
 * JSS API endpoints
 * All endpoints follow the centralized axios instance pattern
 */
export const jssAPI = {
  /**
   * Health check endpoint
   */
  getHealth: async (): Promise<HealthResponse | null> => {
    return handleDirectApiCall(() =>
      axiosInstance.get<HealthResponse>('/health')
    );
  },

  /**
   * Get list of available JSS instances
   */
  getInstances: async (includeStats: boolean = false): Promise<InstanceInfo[] | null> => {
    return handleDirectApiCall(() =>
      axiosInstance.get<InstanceInfo[]>('/instances', {
        params: { include_stats: includeStats }
      })
    );
  },

  /**
   * Get list of available controllers
   */
  getControllers: async (includeStats: boolean = false): Promise<ControllerInfo[] | null> => {
    return handleDirectApiCall(() =>
      axiosInstance.get<ControllerInfo[]>('/controllers', {
        params: { include_stats: includeStats }
      })
    );
  },

  /**
   * Get detailed information about a specific instance
   */
  getInstanceInfo: async (instanceName: string): Promise<InstanceInfo | null> => {
    return handleDirectApiCall(() =>
      axiosInstance.get<InstanceInfo>(`/instances/${instanceName}/info`)
    );
  },

  /**
   * Get detailed information about a specific controller
   */
  getControllerInfo: async (controllerName: string): Promise<ControllerInfo | null> => {
    return handleDirectApiCall(() =>
      axiosInstance.get<ControllerInfo>(`/controllers/${controllerName}/info`)
    );
  },

  /**
   * Run comprehensive comparison of JSS methods
   */
  runComparison: async (request: ComparisonRequest): Promise<ComparisonResult | null> => {
    return handleDirectApiCall(() =>
      axiosInstance.post<ComparisonResult>('/compare', request)
    );
  },

  /**
   * Run comprehensive comparison in background
   */
  runComparisonBackground: async (request: ComparisonRequest): Promise<BackgroundTaskResponse | null> => {
    return handleDirectApiCall(() =>
      axiosInstance.post<BackgroundTaskResponse>('/compare/background', request)
    );
  },

  /**
   * Get status of a background task
   */
  getTaskStatus: async (taskId: string): Promise<BackgroundTaskStatus | null> => {
    return handleDirectApiCall(() =>
      axiosInstance.get<BackgroundTaskStatus>(`/tasks/${taskId}`)
    );
  },

  /**
   * Get all background tasks
   */
  getAllTasks: async (): Promise<BackgroundTaskStatus[] | null> => {
    return handleDirectApiCall(() =>
      axiosInstance.get<BackgroundTaskStatus[]>('/tasks')
    );
  },

  /**
   * Run a single JSS episode
   */
  runSingleEpisode: async (request: SingleRunRequest): Promise<SingleRunResult | null> => {
    return handleDirectApiCall(() =>
      axiosInstance.post<SingleRunResult>('/run', request)
    );
  },

  /**
   * Generate visualizations for comparison results
   */
  generateVisualizations: async (request: VisualizationRequest): Promise<VisualizationResponse | null> => {
    return handleDirectApiCall(() =>
      axiosInstance.post<VisualizationResponse>('/visualizations', request)
    );
  },

  /**
   * List result files
   */
  listResultFiles: async (pattern?: string): Promise<FileListResponse | null> => {
    return handleDirectApiCall(() =>
      axiosInstance.get<FileListResponse>('/files', {
        params: pattern ? { pattern } : {}
      })
    );
  },

  /**
   * Download a result file
   * Returns the blob for file download
   */
  downloadFile: async (filePath: string): Promise<Blob> => {
    return handleDirectApiCall(() =>
      axiosInstance.get(`/files/download/${filePath}`, {
        responseType: 'blob'
      })
    );
  },
};

/**
 * Type-safe JSS API with proper error handling
 * All methods use the centralized axios instance and follow the API integration rules
 */
export default jssAPI;
