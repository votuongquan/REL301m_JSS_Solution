/**
 * JSS API Types - TypeScript definitions for JSS operations
 * These types correspond to the Python Pydantic models in the backend
 */

// Enums
export enum AgentType {
  HYBRID = 'hybrid',
  LOOKAHEAD = 'lookahead',
  CONTROLLER = 'controller',
}

export enum DispatchingRule {
  SPT = 'SPT',
  FIFO = 'FIFO',
  MWR = 'MWR',
  LWR = 'LWR',
  MOR = 'MOR',
  LOR = 'LOR',
  CR = 'CR',
}

export enum TaskStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

// Base Statistics
export interface InstanceStats {
  name: string;
  num_jobs: number;
  num_machines: number;
  total_operations: number;
  avg_processing_time?: number;
  complexity_score?: number;
}

export interface ControllerStats {
  name: string;
  num_people: number;
  num_machines: number;
  avg_qualifications_per_person: number;
  coverage_percentage: number;
}

// Info Models
export interface InstanceInfo {
  name: string;
  path: string;
  size: string;
  stats?: InstanceStats;
  created_at?: string;
  file_size?: number;
}

export interface ControllerInfo {
  name: string;
  path: string;
  num_people: number;
  num_machines: number;
  stats?: ControllerStats;
  created_at?: string;
  file_size?: number;
}

// Request Models
export interface ComparisonRequest {
  instance_name: string;
  controller_name?: string;
  agents?: AgentType[];
  dispatching_rules?: DispatchingRule[];
  num_episodes?: number;
  include_random_baseline?: boolean;
  include_visualizations?: boolean;
}

export interface SingleRunRequest {
  instance_name: string;
  controller_name?: string;
  agent_type?: AgentType;
  num_people?: number;
}

export interface VisualizationRequest {
  instance_name: string;
  results_id: string;
  visualization_types?: string[];
  format?: string;
}

// Performance and Results
export interface PerformanceMetrics {
  avg_makespan: number;
  std_makespan: number;
  min_makespan: number;
  max_makespan: number;
  avg_reward: number;
  std_reward: number;
  avg_execution_time: number;
  total_episodes: number;
}

export interface ComparisonResult {
  instance_name: string;
  controller_name?: string;
  results: Record<string, PerformanceMetrics>;
  best_method: string;
  best_makespan: number;
  ranking: string[];
  execution_summary: Record<string, unknown>;
}

export interface SingleRunResult {
  instance_name: string;
  controller_name?: string;
  agent_type: string;
  makespan: number;
  total_reward: number;
  execution_time: number;
  schedule: ScheduleTask[];
}

export interface ScheduleTask {
  job_id: number;
  machine_id: number;
  start_time: number;
  end_time: number;
  person_id?: number;
}

// Background Tasks
export interface BackgroundTaskStatus {
  task_id: string;
  status: TaskStatus;
  progress?: number;
  result?: Record<string, unknown>;
  error?: string;
  created_at: string;
  updated_at: string;
}

export interface BackgroundTaskResponse {
  task_id: string;
  status: string;
}

// Health and System
export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  uptime?: number;
  available_instances?: number;
  available_controllers?: number;
}

// File Operations
export interface FileListResponse {
  files: string[];
}

export interface VisualizationResponse {
  visualization_paths: string[];
}

// Error Response
export interface ErrorResponse {
  error: string;
  detail?: string;
  code?: number;
}
