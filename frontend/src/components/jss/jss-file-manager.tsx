/**
 * JSS File Manager Component
 * Demonstrates proper file management with JSS API
 * Compatible with both traditional and streaming JSS results
 */

'use client';

import { useState, useEffect } from 'react';
import { jssAPI } from '@/apis/jss-api';
import { getErrorMessage } from '@/utils/apiHandler';

interface JssFileManagerProps {
  title: string;
}

function JssFileManager({ title }: JssFileManagerProps) {
  // State management
  const [files, setFiles] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchPattern, setSearchPattern] = useState<string>('');
  const [downloadingFiles, setDownloadingFiles] = useState<Set<string>>(new Set());

  // Load files on component mount
  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async (pattern?: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await jssAPI.listResultFiles(pattern);
      setFiles(response?.files || []);
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(`Failed to load files: ${errorMessage}`);
      console.error('Failed to load files:', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    await loadFiles(searchPattern || undefined);
  };

  const downloadFile = async (filePath: string) => {
    setDownloadingFiles(prev => new Set(prev).add(filePath));
    setError(null);

    try {
      const blob = await jssAPI.downloadFile(filePath);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Safely extract filename from path
      const fileName = getFileName(filePath);
      link.download = fileName;
      
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(`Failed to download file: ${errorMessage}`);
      console.error('Failed to download file:', errorMessage);
    } finally {
      setDownloadingFiles(prev => {
        const newSet = new Set(prev);
        newSet.delete(filePath);
        return newSet;
      });
    }
  };

  const refreshFiles = () => {
    loadFiles(searchPattern || undefined);
  };

  // Helper function to safely extract filename from path
  const getFileName = (filePath: string): string => {
    if (!filePath || typeof filePath !== 'string') return 'unknown-file';
    return filePath.includes('/') ? filePath.split('/').pop() || 'unknown-file' : filePath;
  };

  const formatFileSize = (filePath: string): string => {
    // This would ideally come from the API, but we'll estimate based on file type
    if (!filePath || typeof filePath !== 'string') return 'Unknown';
    
    const extension = filePath.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'csv':
        return '~50KB';
      case 'png':
      case 'jpg':
      case 'jpeg':
        return '~200KB';
      case 'txt':
        return '~10KB';
      default:
        return 'Unknown';
    }
  };

  const getFileIcon = (filePath: string): string => {
    if (!filePath || typeof filePath !== 'string') return '📎';
    
    const extension = filePath.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'csv':
        return '📊';
      case 'png':
      case 'jpg':
      case 'jpeg':
        return '🖼️';
      case 'txt':
        return '📄';
      case 'pdf':
        return '📕';
      default:
        return '📎';
    }
  };

  const getFileType = (filePath: string): string => {
    if (!filePath || typeof filePath !== 'string') return 'File';
    
    const extension = filePath.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'csv':
        return 'Data File';
      case 'png':
      case 'jpg':
      case 'jpeg':
        return 'Image';
      case 'txt':
        return 'Text File';
      case 'pdf':
        return 'PDF Document';
      default:
        return 'File';
    }
  };

  return (
    <div className="bg-[color:var(--background)] text-[color:var(--foreground)] p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">{title}</h1>
        <p className="text-[color:var(--muted-foreground)]">
          Browse and download JSS comparison results and visualizations
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6">
          <p>{error}</p>
        </div>
      )}

      {/* Search and Controls */}
      <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-4 mb-4">
          <form onSubmit={handleSearch} className="flex-1 flex gap-2">
            <input
              type="text"
              value={searchPattern}
              onChange={(e) => setSearchPattern(e.target.value)}
              placeholder="Search files (e.g., *.csv, *dashboard*, dmu16*)"
              className="flex-1 p-2 border border-[color:var(--border)] rounded-md bg-[color:var(--background)]"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              Search
            </button>
          </form>

          <button
            onClick={refreshFiles}
            disabled={loading}
            className="px-6 py-2 bg-[color:var(--muted)] text-[color:var(--muted-foreground)] rounded-md hover:bg-[color:var(--accent)]"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {(() => {
          const validFiles = files.filter(f => typeof f === 'string' && f.length > 0);
          return (
            <div className="text-sm text-[color:var(--muted-foreground)]">
              Found {validFiles.length} file{validFiles.length !== 1 ? 's' : ''}
              {searchPattern && ` matching "${searchPattern}"`}
            </div>
          );
        })()}
      </div>

      {/* Files List */}
      <div className="bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-6">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2">Loading files...</span>
          </div>
        ) : (
          (() => {
            const validFiles = files.filter((filePath): filePath is string =>
              typeof filePath === 'string' && filePath.length > 0
            );

            if (validFiles.length === 0) {
              return (
                <div className="text-center py-8 text-[color:var(--muted-foreground)]">
                  {searchPattern ? 'No files match your search criteria' : 'No files found'}
                </div>
              );
            }

            return (
              <div className="space-y-2">
                {validFiles.map((filePath) => (
                  <div
                    key={filePath}
                    className="flex items-center justify-between p-4 border border-[color:var(--border)] rounded-lg hover:bg-[color:var(--muted)] transition-colors"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <span className="text-2xl">{getFileIcon(filePath)}</span>
                      <div className="min-w-0 flex-1">
                        <div className="font-medium truncate" title={filePath}>
                          {getFileName(filePath)}
                        </div>
                        <div className="text-sm text-[color:var(--muted-foreground)] flex gap-4">
                          <span>{getFileType(filePath)}</span>
                          <span>{formatFileSize(filePath)}</span>
                          <span className="truncate" title={filePath}>
                            {filePath}
                          </span>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => downloadFile(filePath)}
                      disabled={downloadingFiles.has(filePath)}
                      className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {downloadingFiles.has(filePath) ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          Downloading...
                        </>
                      ) : (
                        <>
                          ⬇️ Download
                        </>
                      )}
                    </button>
                  </div>
                ))}
              </div>
            );
          })()
        )}
      </div>

      {/* File Categories */}
      <div className="mt-6 bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">File Categories</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 border border-[color:var(--border)] rounded-lg">
            <div className="text-3xl mb-2">📊</div>
            <div className="font-medium">Data Files</div>
            <div className="text-sm text-[color:var(--muted-foreground)]">
              CSV results, performance metrics
            </div>
          </div>
          <div className="text-center p-4 border border-[color:var(--border)] rounded-lg">
            <div className="text-3xl mb-2">🖼️</div>
            <div className="font-medium">Visualizations</div>
            <div className="text-sm text-[color:var(--muted-foreground)]">
              Charts, dashboards, Gantt charts
            </div>
          </div>
          <div className="text-center p-4 border border-[color:var(--border)] rounded-lg">
            <div className="text-3xl mb-2">📄</div>
            <div className="font-medium">Reports</div>
            <div className="text-sm text-[color:var(--muted-foreground)]">
              Text summaries, performance reports
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default JssFileManager;
