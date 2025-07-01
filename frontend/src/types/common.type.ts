
// Common response matching the Python APIResponse
export interface CommonResponse<T = unknown> {
  error_code: number;
  message: string;
  description?: string;
  data?: T | null;
}

// Api error response
export interface ApiError {
  status: number;
  error_code: number;
  message: string;
  errors?: Record<string, string[]>;
}

// Loading states for API calls
export type LoadingState = 'idle' | 'loading' | 'succeeded' | 'failed';

// Generic API response type
export type ApiResponse<T> = Promise<CommonResponse<T>>;