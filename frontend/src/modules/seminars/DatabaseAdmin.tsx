import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Database, 
  Download, 
  Upload, 
  Trash2, 
  RefreshCw, 
  AlertTriangle,
  CheckCircle,
  X,
  FileJson,
  HardDrive,
  Clock,
  Shield
} from 'lucide-react';
import { fetchWithAuth } from '@/api/client';
import { formatDistanceToNow } from 'date-fns';

interface DatabaseStatus {
  database_path: string;
  database_size_bytes: number;
  last_modified: string;
  tables: { name: string; record_count: number }[];
  total_records: number;
}

interface ConfirmationResponse {
  token: string;
  expires_at: string;
  message: string;
}

export function DatabaseAdmin() {
  const queryClient = useQueryClient();
  const [activeModal, setActiveModal] = useState<'backup' | 'restore' | 'reset' | 'reset-synthetic' | null>(null);
  const [confirmationToken, setConfirmationToken] = useState<string | null>(null);
  const [confirmationMessage, setConfirmationMessage] = useState<string>('');
  const [restoreFile, setRestoreFile] = useState<File | null>(null);
  const [operationSuccess, setOperationSuccess] = useState<{message: string; details?: any} | null>(null);

  // Fetch database status
  const { data: status, isLoading } = useQuery<DatabaseStatus>({
    queryKey: ['database-status'],
    queryFn: async () => {
      const response = await fetchWithAuth('/api/admin/db/status');
      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Only owners can access database administration');
        }
        throw new Error('Failed to fetch database status');
      }
      return response.json();
    },
  });

  // Backup mutation
  const backupMutation = useMutation({
    mutationFn: async () => {
      const response = await fetchWithAuth('/api/admin/db/backup', {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Backup failed');
      return response.blob();
    },
    onSuccess: (blob) => {
      // Download the file
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `seminars_backup_${new Date().toISOString().split('T')[0]}.db`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      setOperationSuccess({ message: 'Database backup downloaded successfully' });
      setActiveModal(null);
    },
    onError: (error: Error) => {
      alert(`Backup failed: ${error.message}`);
    },
  });

  // Request confirmation token mutation
  const requestConfirmationMutation = useMutation({
    mutationFn: async (operation: 'reset' | 'reset_synthetic' | 'restore') => {
      const response = await fetchWithAuth('/api/admin/db/reset/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ operation }),
      });
      if (!response.ok) throw new Error('Failed to get confirmation token');
      return response.json() as Promise<ConfirmationResponse>;
    },
    onSuccess: (data) => {
      setConfirmationToken(data.token);
      setConfirmationMessage(data.message);
    },
    onError: (error: Error) => {
      alert(`Error: ${error.message}`);
    },
  });

  // Upload restore file mutation
  const uploadRestoreMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetchWithAuth('/api/admin/db/restore/upload', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }
      return response.json() as Promise<ConfirmationResponse>;
    },
    onSuccess: (data) => {
      setConfirmationToken(data.token);
      setConfirmationMessage(data.message);
    },
    onError: (error: Error) => {
      alert(`Upload failed: ${error.message}`);
    },
  });

  // Confirm reset mutation
  const confirmResetMutation = useMutation({
    mutationFn: async ({ token, synthetic }: { token: string; synthetic: boolean }) => {
      const response = await fetchWithAuth(`/api/admin/db/reset/confirm?synthetic=${synthetic}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirmation_token: token }),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Reset failed');
      }
      return response.json();
    },
    onSuccess: (data) => {
      setOperationSuccess({
        message: data.message,
        details: data.synthetic_stats
      });
      setActiveModal(null);
      setConfirmationToken(null);
      queryClient.invalidateQueries({ queryKey: ['database-status'] });
      queryClient.invalidateQueries({ queryKey: ['seminars'] });
      queryClient.invalidateQueries({ queryKey: ['speakers'] });
      queryClient.invalidateQueries({ queryKey: ['semester-plans'] });
    },
    onError: (error: Error) => {
      alert(`Reset failed: ${error.message}`);
    },
  });

  // Confirm restore mutation
  const confirmRestoreMutation = useMutation({
    mutationFn: async ({ token, filename }: { token: string; filename: string }) => {
      const response = await fetchWithAuth('/api/admin/db/restore/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          confirmation_token: token,
          original_filename: filename 
        }),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Restore failed');
      }
      return response.json();
    },
    onSuccess: (data) => {
      setOperationSuccess({
        message: data.message,
        details: { backup: data.pre_restore_backup }
      });
      setActiveModal(null);
      setConfirmationToken(null);
      setRestoreFile(null);
      queryClient.invalidateQueries({ queryKey: ['database-status'] });
      queryClient.invalidateQueries({ queryKey: ['seminars'] });
      queryClient.invalidateQueries({ queryKey: ['speakers'] });
      queryClient.invalidateQueries({ queryKey: ['semester-plans'] });
    },
    onError: (error: Error) => {
      alert(`Restore failed: ${error.message}`);
    },
  });

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleBackup = () => {
    setActiveModal('backup');
    backupMutation.mutate();
  };

  const handleRestoreClick = () => {
    setActiveModal('restore');
    setRestoreFile(null);
    setConfirmationToken(null);
  };

  const handleResetClick = () => {
    setActiveModal('reset');
    setConfirmationToken(null);
  };

  const handleResetSyntheticClick = () => {
    setActiveModal('reset-synthetic');
    setConfirmationToken(null);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.db')) {
        alert('Please select a valid SQLite database file (.db)');
        return;
      }
      setRestoreFile(file);
      uploadRestoreMutation.mutate(file);
    }
  };

  const requestConfirmation = () => {
    if (activeModal === 'reset') {
      requestConfirmationMutation.mutate('reset');
    } else if (activeModal === 'reset-synthetic') {
      requestConfirmationMutation.mutate('reset_synthetic');
    }
  };

  const executeOperation = () => {
    if (!confirmationToken) return;
    
    if (activeModal === 'reset') {
      confirmResetMutation.mutate({ token: confirmationToken, synthetic: false });
    } else if (activeModal === 'reset-synthetic') {
      confirmResetMutation.mutate({ token: confirmationToken, synthetic: true });
    } else if (activeModal === 'restore' && restoreFile) {
      confirmRestoreMutation.mutate({ 
        token: confirmationToken, 
        filename: restoreFile.name 
      });
    }
  };

  const closeModal = () => {
    setActiveModal(null);
    setConfirmationToken(null);
    setConfirmationMessage('');
    setRestoreFile(null);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 animate-spin text-primary-600" />
        <span className="ml-2 text-gray-600">Loading database status...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Success Message */}
      {operationSuccess && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-xl">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
            <div>
              <p className="font-medium text-green-900">{operationSuccess.message}</p>
              {operationSuccess.details && (
                <pre className="mt-2 text-sm text-green-800 bg-green-100 p-2 rounded">
                  {JSON.stringify(operationSuccess.details, null, 2)}
                </pre>
              )}
            </div>
            <button 
              onClick={() => setOperationSuccess(null)}
              className="ml-auto text-green-600 hover:text-green-800"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Database Status Card */}
      {status && (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-primary-600" />
            Database Status
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 text-gray-600 mb-1">
                <HardDrive className="w-4 h-4" />
                <span className="text-sm">Size</span>
              </div>
              <p className="text-2xl font-semibold text-gray-900">{formatBytes(status.database_size_bytes)}</p>
            </div>
            
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 text-gray-600 mb-1">
                <FileJson className="w-4 h-4" />
                <span className="text-sm">Total Records</span>
              </div>
              <p className="text-2xl font-semibold text-gray-900">{status.total_records.toLocaleString()}</p>
            </div>
            
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 text-gray-600 mb-1">
                <Clock className="w-4 h-4" />
                <span className="text-sm">Last Modified</span>
              </div>
              <p className="text-lg font-semibold text-gray-900">
                {formatDistanceToNow(new Date(status.last_modified), { addSuffix: true })}
              </p>
            </div>
          </div>

          {/* Tables breakdown */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Tables</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {status.tables.filter(t => t.record_count > 0).map((table) => (
                <div key={table.name} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                  <span className="text-gray-600">{table.name}</span>
                  <span className="font-medium text-gray-900">{table.record_count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 text-xs text-gray-500">
            <code>{status.database_path}</code>
          </div>
        </div>
      )}

      {/* Admin Actions */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-primary-600" />
          Database Administration
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Backup */}
          <button
            onClick={handleBackup}
            disabled={backupMutation.isPending}
            className="flex items-center gap-4 p-4 border border-gray-200 rounded-xl hover:border-primary-300 hover:bg-primary-50 transition-colors text-left"
          >
            <div className="p-3 bg-blue-100 rounded-lg">
              <Download className="w-6 h-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-medium text-gray-900">Backup Database</h3>
              <p className="text-sm text-gray-600">Download a complete backup of the database</p>
            </div>
          </button>

          {/* Restore */}
          <button
            onClick={handleRestoreClick}
            className="flex items-center gap-4 p-4 border border-gray-200 rounded-xl hover:border-amber-300 hover:bg-amber-50 transition-colors text-left"
          >
            <div className="p-3 bg-amber-100 rounded-lg">
              <Upload className="w-6 h-6 text-amber-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-medium text-gray-900">Restore Database</h3>
              <p className="text-sm text-gray-600">Replace database with a backup file</p>
            </div>
          </button>

          {/* Reset All */}
          <button
            onClick={handleResetClick}
            className="flex items-center gap-4 p-4 border border-gray-200 rounded-xl hover:border-red-300 hover:bg-red-50 transition-colors text-left"
          >
            <div className="p-3 bg-red-100 rounded-lg">
              <Trash2 className="w-6 h-6 text-red-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-medium text-gray-900">Reset All Data</h3>
              <p className="text-sm text-gray-600">Delete everything permanently</p>
            </div>
          </button>

          {/* Reset with Synthetic */}
          <button
            onClick={handleResetSyntheticClick}
            className="flex items-center gap-4 p-4 border border-gray-200 rounded-xl hover:border-green-300 hover:bg-green-50 transition-colors text-left"
          >
            <div className="p-3 bg-green-100 rounded-lg">
              <RefreshCw className="w-6 h-6 text-green-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-medium text-gray-900">Reset with Synthetic Data</h3>
              <p className="text-sm text-gray-600">Clear and populate with test data</p>
            </div>
          </button>
        </div>

        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5" />
          <p className="text-sm text-yellow-800">
            These operations require owner privileges. All destructive actions create emergency backups and require confirmation tokens.
          </p>
        </div>
      </div>

      {/* Modals */}
      {activeModal === 'backup' && backupMutation.isPending && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="w-8 h-8 animate-spin text-primary-600" />
              <span className="ml-3 text-gray-600">Creating backup...</span>
            </div>
          </div>
        </div>
      )}

      {activeModal === 'restore' && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Restore Database</h2>
              <button onClick={closeModal} className="p-1 hover:bg-gray-100 rounded">
                <X className="w-5 h-5" />
              </button>
            </div>

            {!confirmationToken ? (
              <div className="space-y-4">
                <p className="text-sm text-gray-600">
                  Select a SQLite database file (.db) to restore. This will <strong>replace</strong> the current database.
                </p>
                
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <input
                    type="file"
                    accept=".db"
                    onChange={handleFileUpload}
                    disabled={uploadRestoreMutation.isPending}
                    className="hidden"
                    id="restore-file"
                  />
                  <label 
                    htmlFor="restore-file"
                    className="cursor-pointer flex flex-col items-center"
                  >
                    <Upload className="w-8 h-8 text-gray-400 mb-2" />
                    <span className="text-sm text-gray-600">
                      {uploadRestoreMutation.isPending ? 'Uploading...' : 'Click to select database file'}
                    </span>
                  </label>
                </div>

                {uploadRestoreMutation.isError && (
                  <p className="text-sm text-red-600">
                    {(uploadRestoreMutation.error as Error).message}
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-amber-900">Confirm Restore</p>
                      <p className="text-sm text-amber-800 mt-1">{confirmationMessage}</p>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={closeModal}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={executeOperation}
                    disabled={confirmRestoreMutation.isPending}
                    className="flex-1 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50"
                  >
                    {confirmRestoreMutation.isPending ? 'Restoring...' : 'Confirm Restore'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {(activeModal === 'reset' || activeModal === 'reset-synthetic') && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">
                {activeModal === 'reset-synthetic' ? 'Reset with Synthetic Data' : 'Reset All Data'}
              </h2>
              <button onClick={closeModal} className="p-1 hover:bg-gray-100 rounded">
                <X className="w-5 h-5" />
              </button>
            </div>

            {!confirmationToken ? (
              <div className="space-y-4">
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-red-900">Warning: Destructive Action</p>
                      <p className="text-sm text-red-800 mt-1">
                        {activeModal === 'reset-synthetic' 
                          ? 'This will delete ALL data and create fresh synthetic test data.'
                          : 'This will permanently delete ALL data from the database.'}
                      </p>
                    </div>
                  </div>
                </div>

                <p className="text-sm text-gray-600">
                  An emergency backup will be created before the operation. You will need to confirm with a token.
                </p>

                <button
                  onClick={requestConfirmation}
                  disabled={requestConfirmationMutation.isPending}
                  className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                >
                  {requestConfirmationMutation.isPending ? 'Requesting...' : 'Request Confirmation'}
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-amber-900">Final Confirmation</p>
                      <p className="text-sm text-amber-800 mt-1">{confirmationMessage}</p>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={closeModal}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={executeOperation}
                    disabled={confirmResetMutation.isPending}
                    className={`flex-1 px-4 py-2 text-white rounded-lg disabled:opacity-50 ${
                      activeModal === 'reset-synthetic' 
                        ? 'bg-green-600 hover:bg-green-700' 
                        : 'bg-red-600 hover:bg-red-700'
                    }`}
                  >
                    {confirmResetMutation.isPending ? 'Resetting...' : 'Confirm Reset'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
