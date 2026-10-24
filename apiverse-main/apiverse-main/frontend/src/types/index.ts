export interface DashboardMetrics {
  tagline: string;
  counts: {
    repositories: number;
    specifications: number;
    scans: number;
    breaking_changes: number;
    warnings: number;
    total_repairs: number;
    approved_repairs: number;
    open_prs: number;
    active_monitors: number;
    unread_notifications: number;
  };
  recent_scans: Array<{
    id: number;
    created_at: string;
    repository: string;
    previous_spec: string;
    current_spec: string;
    status: string;
    breaking_changes: number;
    total_changes: number;
  }>;
}

export interface Repository {
  id: number;
  name: string;
  full_name: string;
  clone_url?: string;
  default_branch: string;
  is_demo: boolean;
  github_id?: number;
  local_path?: string;
  last_synced_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ApiSpecification {
  id: number;
  name: string;
  version: string;
  format: string;
  source_type: string;
  source_url?: string;
  created_at: string;
  content_json: string;
}

export interface DetectedChange {
  id: number;
  scan_id: number;
  change_type: string;
  severity: 'BREAKING' | 'WARNING' | 'INFO';
  path: string;
  http_method?: string;
  description: string;
  rule_code: string;
  old_value?: string;
  new_value?: string;
  evidence_json: string;
  status: string;
  created_at: string;
}

export interface ScanDetail {
  id: number;
  repository_id?: number;
  previous_spec_id: number;
  current_spec_id: number;
  status: string;
  total_changes: number;
  breaking_changes: number;
  warnings: number;
  infos: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
  detected_changes: DetectedChange[];
}

export interface AffectedFile {
  id: number;
  detected_change_id: number;
  repository_id: number;
  file_path: string;
  language: string;
  function_name?: string;
  line_start: number;
  line_end: number;
  match_confidence: 'confirmed' | 'possible';
  snippet: string;
  context_reason?: string;
  created_at: string;
}

export interface ProposedPatch {
  id: number;
  repair_attempt_id: number;
  file_path: string;
  original_content: string;
  patched_content: string;
  unified_diff: string;
  is_valid: boolean;
  validation_error?: string;
  created_at: string;
}

export interface RepairAttempt {
  id: number;
  detected_change_id: number;
  status: string;
  provider: string;
  model_name: string;
  explanation?: string;
  reasoning?: string;
  known_risks?: string;
  developer_approved: boolean;
  approved_at?: string;
  created_at: string;
  updated_at: string;
  patches: ProposedPatch[];
}

export interface TestRun {
  id: number;
  repair_attempt_id: number;
  repository_id: number;
  command: string;
  exit_code?: number;
  stdout?: string;
  stderr?: string;
  duration_seconds: number;
  status: 'passed' | 'failed' | 'timeout' | 'skipped' | 'not_run';
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  created_at: string;
}

export interface PullRequestRecord {
  id: number;
  repair_attempt_id: number;
  repository_id: number;
  pr_number?: number;
  pr_url?: string;
  branch_name: string;
  base_branch: string;
  title: string;
  body: string;
  commit_hash?: string;
  status: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface MonitoringConfig {
  id: number;
  repository_id: number;
  name: string;
  api_spec_url: string;
  schedule_cron?: string;
  interval_minutes: number;
  is_active: boolean;
  webhook_secret?: string;
  auto_repair: boolean;
  auto_pr: boolean;
  last_run_at?: string;
  next_run_at?: string;
  created_at: string;
}

export interface BackgroundJob {
  id: number;
  monitoring_id?: number;
  job_type: string;
  status: string;
  started_at: string;
  finished_at?: string;
  logs?: string;
  error_message?: string;
}

export interface NotificationRecord {
  id: number;
  event_type: string;
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'success';
  is_read: boolean;
  metadata_json?: string;
  created_at: string;
}

export interface SystemConfigStatus {
  llm_provider: string;
  llm_configured: boolean;
  github_app_configured: boolean;
  github_pat_configured: boolean;
  developer_approval_required: boolean;
  database_path: string;
  demo_repos_path: string;
  sandbox_path: string;
}

export interface SystemHealth {
  status: string;
  version: string;
  database: string;
  scheduler: string;
  tagline: string;
}
