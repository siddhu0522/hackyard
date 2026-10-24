import React from 'react';
import {
  FolderGit2,
  FileCode2,
  AlertTriangle,
  GitPullRequest,
  Play,
  Clock,
  CheckCircle2,
  ChevronRight,
  GitBranch
} from 'lucide-react';
import { DashboardMetrics, ScanDetail, PullRequestRecord, NotificationRecord } from '../types';
import { TabKey } from '../components/Sidebar';

interface DashboardViewProps {
  metrics: DashboardMetrics | null;
  scans: ScanDetail[];
  pullRequests: PullRequestRecord[];
  notifications: NotificationRecord[];
  onNavigate: (tab: TabKey) => void;
  onInspectScan: (scanId: number) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  metrics,
  scans,
  pullRequests,
  notifications,
  onNavigate,
  onInspectScan,
}) => {
  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-96 text-[#625F4B] text-xs">
        <div className="flex items-center space-x-2">
          <span className="h-2.5 w-2.5 rounded-full bg-[#6D28D9] animate-ping"></span>
          <span className="font-medium">Loading APIVerse telemetry...</span>
        </div>
      </div>
    );
  }

  const latestScan = scans.length > 0 ? scans[0] : null;
  const recentChanges = latestScan?.detected_changes?.slice(0, 4) || [];
  const latestPrs = pullRequests.slice(0, 3);

  // Compute actual severity counts for chart
  const breakingTotal = metrics.counts.breaking_changes || 0;
  const warningsTotal = metrics.counts.warnings || 0;
  const totalReported = breakingTotal + warningsTotal || 1;
  const breakingPct = Math.round((breakingTotal / totalReported) * 100);
  const warningPct = Math.round((warningsTotal / totalReported) * 100);

  return (
    <div className="space-y-6">
      {/* A. Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-responsive-title font-bold text-[#282719] tracking-tight">Overview</h1>
          <p className="text-responsive-body text-[#625F4B] mt-1">
            Monitor API compatibility, investigate breaking changes, and manage autonomous repairs.
          </p>
        </div>

        <div className="flex items-center space-x-2.5 self-start sm:self-auto">
          <button
            onClick={() => onNavigate('repositories')}
            className="flex items-center space-x-1.5 rounded-lg bg-white hover:bg-[#E6D9A0] px-3.5 py-2 text-xs font-semibold text-[#282719] border border-[#DCD3A5] shadow-2xs transition-colors"
          >
            <FolderGit2 className="h-3.5 w-3.5 text-[#625F4B]" />
            <span>Connect Repository</span>
          </button>

          <button
            onClick={() => onNavigate('specs')}
            className="flex items-center space-x-1.5 rounded-lg bg-[#6D28D9] hover:bg-[#5B21B6] px-4 py-2 text-xs font-semibold text-white shadow-xs transition-all"
          >
            <Play className="h-3 w-3 fill-current" />
            <span>New Scan</span>
          </button>
        </div>
      </div>

      {/* B. Telemetry Overview Panel */}
      <div className="apv-panel-elevated p-4 sm:p-5 apv-panel-glow">
        <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-[#DCD3A5] gap-4 md:gap-0">
          {/* Group 1: Workspace & Target */}
          <div className="md:pr-5 space-y-1.5 pb-3 md:pb-0">
            <span className="text-[11px] uppercase font-bold tracking-wider text-[#77735D]">
              Target Client Repository
            </span>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-bold text-[#282719]">payment-service-py</span>
              <span className="rounded bg-[#FFFCD3] px-1.5 py-0.5 text-[10px] font-mono font-semibold text-[#6D28D9] border border-[#DCD3A5]">
                demo/local
              </span>
            </div>
            <div className="text-xs text-[#625F4B] font-mono flex items-center space-x-1">
              <GitBranch className="h-3.5 w-3.5 text-[#77735D]" />
              <span>default branch: main</span>
            </div>
          </div>

          {/* Group 2: Latest Scan Status */}
          <div className="md:px-5 space-y-1.5 pt-3 md:pt-0 pb-3 md:pb-0">
            <span className="text-[11px] uppercase font-bold tracking-wider text-[#77735D]">
              Latest Contract Diff
            </span>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-bold text-[#282719]">
                {latestScan ? `Scan #${latestScan.id}` : 'No scans executed'}
              </span>
              {latestScan && (
                <span className="rounded bg-[#DCFCE7] px-2 py-0.5 text-[10px] font-bold text-[#15803D] border border-[#BBF7D0] uppercase">
                  {latestScan.status}
                </span>
              )}
            </div>
            <div className="text-xs text-[#625F4B] flex items-center space-x-1">
              <Clock className="h-3.5 w-3.5 text-[#77735D]" />
              <span>
                {latestScan?.created_at ? new Date(latestScan.created_at).toLocaleTimeString() : 'Awaiting trigger'}
              </span>
            </div>
          </div>

          {/* Group 3: Compatibility & Outstanding Changes */}
          <div className="md:pl-5 space-y-1.5 pt-3 md:pt-0">
            <span className="text-[11px] uppercase font-bold tracking-wider text-[#77735D]">
              API Compatibility Status
            </span>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-bold text-[#DC2626]">
                {metrics.counts.breaking_changes} Breaking Changes
              </span>
            </div>
            <div className="text-xs text-[#625F4B]">
              {metrics.counts.approved_repairs} repairs approved • {metrics.counts.open_prs} reviewable PRs
            </div>
          </div>
        </div>
      </div>

      {/* C. 4 Summary KPI Metric Panels */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          onClick={() => onNavigate('repositories')}
          className="apv-panel p-4 hover:border-[#C4B982] cursor-pointer transition-all hover:shadow-sm"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#625F4B]">Connected Repositories</span>
            <FolderGit2 className="h-4 w-4 text-[#77735D]" />
          </div>
          <div className="mt-2 text-responsive-metric font-bold text-[#282719]">{metrics.counts.repositories}</div>
          <div className="mt-1 text-xs text-[#77735D]">100% indexed &amp; ready</div>
        </div>

        <div
          onClick={() => onNavigate('specs')}
          className="apv-panel p-4 hover:border-[#C4B982] cursor-pointer transition-all hover:shadow-sm"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#625F4B]">Total Scans Executed</span>
            <FileCode2 className="h-4 w-4 text-[#6D28D9]" />
          </div>
          <div className="mt-2 text-responsive-metric font-bold text-[#282719]">{metrics.counts.scans}</div>
          <div className="mt-1 text-xs text-[#77735D]">OpenAPI 3.0 &amp; 3.1</div>
        </div>

        <div
          onClick={() => onNavigate('changes')}
          className="apv-panel p-4 hover:border-[#C4B982] cursor-pointer transition-all hover:shadow-sm border-l-4 border-l-[#DC2626]"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#625F4B]">Open Breaking Changes</span>
            <AlertTriangle className="h-4 w-4 text-[#DC2626]" />
          </div>
          <div className="mt-2 text-responsive-metric font-bold text-[#DC2626]">{metrics.counts.breaking_changes}</div>
          <div className="mt-1 text-xs text-[#77735D]">Requires client adaptation</div>
        </div>

        <div
          onClick={() => onNavigate('pull_requests')}
          className="apv-panel p-4 hover:border-[#C4B982] cursor-pointer transition-all hover:shadow-sm border-l-4 border-l-[#6D28D9]"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#625F4B]">PRs Awaiting Review</span>
            <GitPullRequest className="h-4 w-4 text-[#6D28D9]" />
          </div>
          <div className="mt-2 text-responsive-metric font-bold text-[#282719]">{metrics.counts.open_prs}</div>
          <div className="mt-1 text-xs text-[#77735D]">Verified in isolated sandbox</div>
        </div>
      </div>

      {/* D. Main Workspace: Primary Area (8 cols) + Secondary Area (4 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Primary Area (8 Cols) - Left-side panel */}
        <div className="lg:col-span-8 space-y-6 w-full min-w-0">
          {/* Severity Breakdown Bar */}
          <div className="apv-panel p-5 space-y-3.5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
              <div>
                <h2 className="text-responsive-card font-bold text-[#282719] tracking-tight">
                  Detected Change Classification Distribution
                </h2>
                <p className="text-xs text-[#625F4B] mt-0.5">
                  Severity breakdown across analyzed endpoints
                </p>
              </div>
              <span className="text-xs text-[#625F4B] font-mono self-start sm:self-auto">
                {breakingTotal} Breaking • {warningsTotal} Warnings
              </span>
            </div>

            <div className="h-2.5 w-full rounded-full bg-[#FFFCD3] border border-[#DCD3A5] overflow-hidden flex">
              <div
                style={{ width: `${breakingPct}%` }}
                className="bg-[#DC2626] h-full transition-all duration-500"
                title={`${breakingTotal} Breaking Changes`}
              ></div>
              <div
                style={{ width: `${warningPct}%` }}
                className="bg-[#B45309] h-full transition-all duration-500"
                title={`${warningsTotal} Warnings`}
              ></div>
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs text-[#625F4B] pt-1">
              <span className="flex items-center space-x-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-[#DC2626]"></span>
                <span className="font-medium text-[#282719]">Breaking (Incompatible contract changes)</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-[#B45309]"></span>
                <span className="font-medium text-[#282719]">Warnings (Deprecations / modifications)</span>
              </span>
            </div>
          </div>

          {/* Recent Scans Table */}
          <div className="apv-panel p-5 space-y-3.5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-responsive-card font-bold text-[#282719]">
                  Recent API Specification Scans
                </h2>
                <p className="text-xs text-[#625F4B] mt-0.5">OpenAPI version comparison records</p>
              </div>
              <button
                onClick={() => onNavigate('specs')}
                className="text-xs text-[#6D28D9] hover:text-[#5B21B6] font-semibold"
              >
                View all specs →
              </button>
            </div>

            <div className="overflow-x-auto rounded-lg border border-[#DCD3A5]">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#FFFCD3]/80 border-b border-[#DCD3A5] text-[#625F4B] text-[11px] font-bold uppercase tracking-wider">
                  <tr>
                    <th className="py-2.5 px-3 whitespace-nowrap">ID</th>
                    <th className="py-2.5 px-3 whitespace-nowrap">Repository</th>
                    <th className="py-2.5 px-3 whitespace-nowrap">Contract Diff</th>
                    <th className="py-2.5 px-3 whitespace-nowrap">Breaking</th>
                    <th className="py-2.5 px-3 whitespace-nowrap">Status</th>
                    <th className="py-2.5 px-3 text-right whitespace-nowrap">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#DCD3A5]/60 text-[#282719] bg-white">
                  {scans.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-[#77735D]">
                        No scans recorded yet.
                      </td>
                    </tr>
                  ) : (
                    scans.slice(0, 5).map(scan => (
                      <tr key={scan.id} className="hover:bg-[#FFFCD3]/40 transition-colors">
                        <td className="py-3 px-3 font-mono text-[#77735D] whitespace-nowrap">#{scan.id}</td>
                        <td className="py-3 px-3 font-semibold text-[#282719] whitespace-nowrap">payment-service-py</td>
                        <td className="py-3 px-3 font-mono text-[#625F4B] text-[11px] whitespace-nowrap">
                          v1.0.0 → v2.0.0
                        </td>
                        <td className="py-3 px-3 whitespace-nowrap">
                          {scan.breaking_changes > 0 ? (
                            <span className="rounded bg-[#FEE2E2] px-2 py-0.5 text-[10px] font-bold text-[#DC2626] border border-[#FECACA]">
                              {scan.breaking_changes} breaking
                            </span>
                          ) : (
                            <span className="text-[#15803D] font-medium text-[11px]">0 breaking</span>
                          )}
                        </td>
                        <td className="py-3 px-3 whitespace-nowrap">
                          <span className="rounded bg-[#DCFCE7] px-2 py-0.5 text-[10px] font-bold text-[#15803D] border border-[#BBF7D0] uppercase">
                            {scan.status}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-right whitespace-nowrap">
                          <button
                            onClick={() => onInspectScan(scan.id)}
                            className="rounded-lg px-2.5 py-1 text-xs font-semibold text-[#282719] hover:bg-[#E6D9A0] bg-[#FFFCD3] border border-[#DCD3A5] transition-colors"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Active Breaking Changes Quick View */}
          <div className="apv-panel p-5 space-y-3.5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-responsive-card font-bold text-[#282719]">
                  Critical Breaking Changes
                </h2>
                <p className="text-xs text-[#625F4B] mt-0.5">Changes requiring source code adaptation</p>
              </div>
              <button
                onClick={() => onNavigate('changes')}
                className="text-xs text-[#6D28D9] hover:text-[#5B21B6] font-semibold"
              >
                Inspect all changes →
              </button>
            </div>

            <div className="space-y-2.5">
              {recentChanges.length === 0 ? (
                <div className="text-center py-6 text-xs text-[#77735D]">
                  No critical changes detected in current scan.
                </div>
              ) : (
                recentChanges.map(c => (
                  <div
                    key={c.id}
                    onClick={() => onNavigate('changes')}
                    className="flex items-center justify-between rounded-xl bg-white p-3.5 border border-[#DCD3A5] hover:border-[#C4B982] hover:bg-[#FFFCD3]/30 cursor-pointer transition-all shadow-2xs"
                  >
                    <div className="space-y-1 min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded bg-[#FEE2E2] px-2 py-0.5 text-[10px] font-bold text-[#DC2626] border border-[#FECACA] shrink-0">
                          {c.change_type}
                        </span>
                        <span className="font-mono text-xs font-bold text-[#282719] truncate">
                          {c.http_method || 'ANY'} {c.path}
                        </span>
                      </div>
                      <p className="text-xs text-[#625F4B] line-clamp-1">{c.description}</p>
                    </div>

                    <ChevronRight className="h-4 w-4 text-[#77735D] shrink-0 ml-3" />
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Secondary Area (4 Cols) */}
        <div className="lg:col-span-4 space-y-6 w-full min-w-0">
          {/* Workflow State Machine Card */}
          <div className="apv-panel p-5 space-y-3.5">
            <div className="flex items-center justify-between">
              <span className="text-responsive-card font-bold text-[#282719]">
                Autonomous Lifecycle
              </span>
              <span className="text-xs text-[#6D28D9] font-mono font-bold bg-[#EDE9FE] px-2 py-0.5 rounded border border-[#DDD6FE]">
                Stage 5/5
              </span>
            </div>

            <div className="space-y-2.5 text-xs">
              {[
                { label: 'Detect Contract Diff', desc: 'OpenAPI 3.0/3.1 comparison' },
                { label: 'Analyze Code Impact', desc: 'AST mapping to client files' },
                { label: 'Synthesize AI Repair', desc: 'Unified diff generation' },
                { label: 'Verify in Sandbox', desc: 'Isolated test execution' },
                { label: 'Reviewable Pull Request', desc: 'Never auto-merged to default' },
              ].map((step, i) => (
                <div
                  key={i}
                  className="flex items-start space-x-3 rounded-lg bg-[#FFFBEA] p-2.5 border border-[#DCD3A5]"
                >
                  <CheckCircle2 className="h-4 w-4 text-[#15803D] shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-[#282719] block text-xs">{step.label}</span>
                    <span className="text-[11px] text-[#625F4B]">{step.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Pull Requests */}
          <div className="apv-panel p-5 space-y-3.5">
            <div className="flex items-center justify-between">
              <span className="text-responsive-card font-bold text-[#282719]">
                Recent Pull Requests
              </span>
              <button
                onClick={() => onNavigate('pull_requests')}
                className="text-xs text-[#6D28D9] hover:text-[#5B21B6] font-semibold"
              >
                View all →
              </button>
            </div>

            <div className="space-y-2.5">
              {latestPrs.length === 0 ? (
                <p className="text-xs text-[#77735D] py-3 text-center">No PRs created yet.</p>
              ) : (
                latestPrs.map(pr => (
                  <div
                    key={pr.id}
                    onClick={() => onNavigate('pull_requests')}
                    className="rounded-xl bg-white p-3.5 border border-[#DCD3A5] hover:border-[#C4B982] hover:bg-[#FFFCD3]/30 cursor-pointer transition-all shadow-2xs"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-mono text-xs font-bold text-[#6D28D9]">
                        PR #{pr.pr_number || pr.id}
                      </span>
                      <span className="rounded bg-[#DCFCE7] px-2 py-0.5 text-[10px] font-bold text-[#15803D] border border-[#BBF7D0] uppercase">
                        {pr.status}
                      </span>
                    </div>
                    <p className="text-xs text-[#282719] line-clamp-1 font-semibold">{pr.title}</p>
                    <div className="mt-2 text-[11px] text-[#77735D] font-mono">
                      {pr.branch_name} → {pr.base_branch}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
