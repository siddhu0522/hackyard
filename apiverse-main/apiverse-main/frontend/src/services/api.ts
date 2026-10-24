import {
  DashboardMetrics,
  Repository,
  ApiSpecification,
  ScanDetail,
  DetectedChange,
  AffectedFile,
  RepairAttempt,
  ProposedPatch,
  TestRun,
  PullRequestRecord,
  MonitoringConfig,
  BackgroundJob,
  NotificationRecord,
  SystemHealth,
  SystemConfigStatus
} from '../types';

const BASE_URL = '/api/v1';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    let errMessage = `Error ${res.status}: ${res.statusText}`;
    try {
      const errData = await res.json();
      if (errData.detail) errMessage = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
    } catch (_) {}
    throw new Error(errMessage);
  }

  return res.json();
}

export const api = {
  // System
  getHealth: () => request<SystemHealth>('/system/health'),
  getConfigStatus: () => request<SystemConfigStatus>('/system/config/status'),
  seedDemoData: () => request<{ status: string; message?: string; stats?: any; summary?: any }>('/system/seed-demo', { method: 'POST' }),

  // Dashboard
  getMetrics: () => request<DashboardMetrics>('/dashboard/metrics'),

  // Repositories
  listRepositories: () => request<Repository[]>('/repositories'),
  discoverDemoRepos: () => request<{ status: string; added: string[]; total_demo_repos: number }>('/repositories/discover-demo', { method: 'POST' }),
  getGitHubStatus: () => request<{ configured: boolean; authenticated: boolean; user?: string; rate_limit_remaining?: number; demo_mode: boolean; message: string }>('/repositories/github/status'),
  getRepoTree: (repoId: number, branch?: string) => request<{ repository: string; branch: string; tree: any[] }>(`/repositories/${repoId}/tree${branch ? `?branch=${branch}` : ''}`),
  getFileContent: (repoId: number, filePath: string, ref?: string) => request<{ file_path: string; content: string }>(`/repositories/${repoId}/file?file_path=${encodeURIComponent(filePath)}${ref ? `&ref=${ref}` : ''}`),

  // Specifications
  listSpecifications: () => request<ApiSpecification[]>('/specifications'),
  getSpecification: (id: number) => request<ApiSpecification>(`/specifications/${id}`),
  createSpecification: (payload: { name: string; version: string; content: string; format: string; source_type: string; source_url?: string }) =>
    request<ApiSpecification>('/specifications', { method: 'POST', body: JSON.stringify(payload) }),
  fetchSpecFromUrl: (url: string, name?: string) =>
    request<ApiSpecification>(`/specifications/fetch-url?url=${encodeURIComponent(url)}${name ? `&name=${encodeURIComponent(name)}` : ''}`, { method: 'POST' }),

  // Scans
  listScans: (repoId?: number) => request<ScanDetail[]>(`/scans${repoId ? `?repository_id=${repoId}` : ''}`),
  getScan: (id: number) => request<ScanDetail>(`/scans/${id}`),
  triggerScan: (payload: { repository_id?: number; previous_spec_id: number; current_spec_id: number }) =>
    request<ScanDetail>('/scans', { method: 'POST', body: JSON.stringify(payload) }),
  getScanChanges: (scanId: number, severity?: string) =>
    request<DetectedChange[]>(`/scans/${scanId}/changes${severity ? `?severity=${severity}` : ''}`),

  // Code Impact
  getAffectedFiles: (changeId: number) => request<AffectedFile[]>(`/impact/affected-files/${changeId}`),
  analyzeCodeImpact: (changeId: number, repoId: number) =>
    request<AffectedFile[]>('/impact/analyze', { method: 'POST', body: JSON.stringify({ detected_change_id: changeId, repository_id: repoId }) }),

  // AI Repairs
  getRepair: (id: number) => request<RepairAttempt>(`/repairs/${id}`),
  getRepairsByChange: (changeId: number) => request<RepairAttempt[]>(`/repairs/by-change/${changeId}`),
  generateRepair: (changeId: number, provider?: string) =>
    request<RepairAttempt>('/repairs/generate', { method: 'POST', body: JSON.stringify({ detected_change_id: changeId, provider }) }),
  approveRepair: (repairId: number, approved: boolean, notes?: string) =>
    request<RepairAttempt>('/repairs/approve', { method: 'POST', body: JSON.stringify({ repair_attempt_id: repairId, approved, notes }) }),
  updatePatch: (patchId: number, patchedContent: string) =>
    request<ProposedPatch>(`/repairs/patches/${patchId}`, { method: 'PUT', body: JSON.stringify({ patch_id: patchId, patched_content: patchedContent }) }),

  // Test Verifications
  getTestRun: (id: number) => request<TestRun>(`/verifications/${id}`),
  getRunsByRepair: (repairId: number) => request<TestRun[]>(`/verifications/by-repair/${repairId}`),
  runVerification: (repairId: number, customCommand?: string) =>
    request<TestRun>('/verifications/run', { method: 'POST', body: JSON.stringify({ repair_attempt_id: repairId, custom_command: customCommand }) }),

  // Pull Requests
  listPullRequests: (repoId?: number) => request<PullRequestRecord[]>(`/pull-requests${repoId ? `?repository_id=${repoId}` : ''}`),
  createPullRequest: (repairId: number, branchName?: string, title?: string) =>
    request<PullRequestRecord>('/pull-requests', { method: 'POST', body: JSON.stringify({ repair_attempt_id: repairId, branch_name: branchName, title }) }),

  // Monitoring & Automation
  listMonitoringConfigs: () => request<MonitoringConfig[]>('/monitoring'),
  createMonitoringConfig: (payload: { repository_id: number; name: string; api_spec_url: string; schedule_cron?: string; interval_minutes: number; is_active: boolean; auto_repair: boolean; auto_pr: boolean }) =>
    request<MonitoringConfig>('/monitoring', { method: 'POST', body: JSON.stringify(payload) }),
  pauseMonitoring: (id: number) => request<MonitoringConfig>(`/monitoring/${id}/pause`, { method: 'POST' }),
  resumeMonitoring: (id: number) => request<MonitoringConfig>(`/monitoring/${id}/resume`, { method: 'POST' }),
  runMonitoringNow: (id: number) => request<BackgroundJob>(`/monitoring/${id}/run-now`, { method: 'POST' }),
  getMonitoringJobs: (id: number) => request<BackgroundJob[]>(`/monitoring/${id}/jobs`),
  listNotifications: () => request<NotificationRecord[]>('/monitoring/notifications'),
  markNotificationRead: (id: number) => request<{ status: string }>(`/monitoring/notifications/${id}/read`, { method: 'POST' }),
};
