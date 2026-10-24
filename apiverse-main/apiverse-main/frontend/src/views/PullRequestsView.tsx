import React, { useState } from 'react';
import {
  GitPullRequest,
  GitBranch,
  ExternalLink,
  Shield,
  Check
} from 'lucide-react';
import { PullRequestRecord } from '../types';

interface PullRequestsViewProps {
  pullRequests: PullRequestRecord[];
  onRefresh: () => void;
}

export const PullRequestsView: React.FC<PullRequestsViewProps> = ({ pullRequests }) => {
  const [selectedPrId, setSelectedPrId] = useState<number | null>(null);

  const activePr = pullRequests.find(p => p.id === selectedPrId) || pullRequests[0];

  const workflowSteps = [
    { label: 'Detect', desc: 'OpenAPI Diff' },
    { label: 'Analyze', desc: 'AST Impact' },
    { label: 'Repair', desc: 'AI Synthesis' },
    { label: 'Verify', desc: 'Sandbox Tests' },
    { label: 'Review', desc: 'PR Published' },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-responsive-title font-bold text-[#282719] flex items-center space-x-2.5">
            <div className="h-7 w-7 rounded-lg bg-[#EDE9FE] border border-[#DDD6FE] flex items-center justify-center">
              <GitPullRequest className="h-4 w-4 text-[#6D28D9]" />
            </div>
            <span>Pull Requests</span>
          </h1>
          <p className="text-responsive-body text-[#625F4B] mt-1">
            Reviewable Pull Requests generated with verification evidence and contract change justification
          </p>
        </div>

        <div className="flex items-center space-x-2 rounded-lg bg-[#DCFCE7] px-3.5 py-1.5 text-xs text-[#15803D] border border-[#BBF7D0] self-start sm:self-auto font-bold">
          <Shield className="h-3.5 w-3.5" />
          <span>Strict Boundary: Never Auto-Merged</span>
        </div>
      </div>

      {/* Workflow State Machine Progression */}
      <div className="rounded-xl bg-white p-4 sm:p-5 border border-[#DCD3A5] shadow-2xs">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold uppercase tracking-wider text-[#77735D]">
            APIVerse Autonomous Lifecycle Pipeline
          </span>
          <span className="text-xs font-mono font-bold text-[#15803D] bg-[#DCFCE7] px-2 py-0.5 rounded border border-[#BBF7D0]">
            State Machine: Complete
          </span>
        </div>
        <div className="flex items-center justify-between overflow-x-auto py-1 gap-2">
          {workflowSteps.map((step, idx) => (
            <React.Fragment key={idx}>
              <div className="flex items-center space-x-2 shrink-0">
                <div className="flex items-center space-x-2 rounded-lg bg-[#FFFBEA] px-3 py-1.5 text-xs border border-[#DCD3A5]">
                  <div className="h-4 w-4 rounded-full bg-[#DCFCE7] border border-[#BBF7D0] flex items-center justify-center">
                    <Check className="h-2.5 w-2.5 text-[#15803D]" />
                  </div>
                  <div>
                    <span className="font-bold text-[#282719]">{step.label}</span>
                    <span className="text-[10px] text-[#625F4B] ml-1.5 font-mono hidden sm:inline">({step.desc})</span>
                  </div>
                </div>
              </div>
              {idx < workflowSteps.length - 1 && (
                <div className="h-0.5 w-6 sm:w-10 bg-[#DCD3A5] shrink-0"></div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {pullRequests.length === 0 ? (
        <div className="rounded-xl border border-[#DCD3A5] bg-white p-12 text-center text-xs text-[#77735D]">
          <GitPullRequest className="h-8 w-8 text-[#77735D] mx-auto mb-3" />
          <p className="text-[#282719] font-bold text-sm">No Pull Requests published yet</p>
          <p className="text-[#625F4B] mt-1">Complete an AI repair synthesis and sandbox test verification run to generate a Pull Request.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* PR Records List */}
          <div className="lg:col-span-5 space-y-3">
            <div className="flex items-center justify-between px-1">
              <h2 className="text-xs font-bold uppercase tracking-wider text-[#77735D]">
                Pull Request Records ({pullRequests.length})
              </h2>
            </div>

            {pullRequests.map(pr => {
              const isSelected = activePr?.id === pr.id;
              return (
                <div
                  key={pr.id}
                  onClick={() => setSelectedPrId(pr.id)}
                  className={`rounded-xl p-4 cursor-pointer transition-all border ${
                    isSelected
                      ? 'border-[#6D28D9] bg-[#FFFCD3] border-l-4 shadow-xs'
                      : 'border-[#DCD3A5] bg-white hover:border-[#C4B982] hover:bg-[#FFFCD3]/30 shadow-2xs'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <GitPullRequest className={`h-4 w-4 ${isSelected ? 'text-[#6D28D9]' : 'text-[#77735D]'}`} />
                      <span className="font-mono text-xs font-bold text-[#6D28D9]">
                        PR #{pr.pr_number || pr.id}
                      </span>
                    </div>
                    <span className="rounded bg-[#DCFCE7] px-2 py-0.5 text-[10px] font-mono font-bold text-[#15803D] border border-[#BBF7D0] uppercase">
                      {pr.status}
                    </span>
                  </div>

                  <h3 className="text-xs font-bold text-[#282719] line-clamp-1">{pr.title}</h3>

                  <div className="mt-2.5 flex items-center space-x-2 text-xs text-[#625F4B] font-mono">
                    <GitBranch className="h-3.5 w-3.5 text-[#6D28D9]" />
                    <span className="text-[#6D28D9] font-semibold">{pr.branch_name}</span>
                    <span className="text-[#77735D]">→</span>
                    <span className="text-[#282719]">{pr.base_branch}</span>
                  </div>

                  <div className="mt-3 flex items-center justify-between text-[11px] text-[#77735D] font-mono border-t border-[#DCD3A5]/60 pt-2">
                    <span>Created: {new Date(pr.created_at).toLocaleDateString()}</span>
                    <span>Repo #{pr.repository_id}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* PR Details and Markdown Body Inspector */}
          <div className="lg:col-span-7 space-y-4">
            {activePr ? (
              <div className="rounded-xl bg-white p-6 border border-[#DCD3A5] space-y-5 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between border-b border-[#DCD3A5] pb-4 gap-3">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs text-[#6D28D9] font-bold">
                        Pull Request #{activePr.pr_number || activePr.id}
                      </span>
                      <span className="rounded bg-[#EDE9FE] px-2 py-0.5 text-[10px] font-mono font-bold text-[#6D28D9] border border-[#DDD6FE]">
                        {activePr.status.toUpperCase()}
                      </span>
                    </div>
                    <h2 className="text-responsive-card font-bold text-[#282719] mt-1.5">{activePr.title}</h2>
                  </div>

                  {activePr.pr_url && (
                    <a
                      href={activePr.pr_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center space-x-1.5 rounded-lg bg-white px-3.5 py-1.5 text-xs font-bold text-[#282719] hover:bg-[#E6D9A0] border border-[#DCD3A5] transition-colors shrink-0 shadow-2xs"
                    >
                      <span>View on GitHub</span>
                      <ExternalLink className="h-3.5 w-3.5 text-[#77735D]" />
                    </a>
                  )}
                </div>

                {/* Branch Merge Route */}
                <div className="space-y-1.5">
                  <span className="text-xs font-bold text-[#77735D] uppercase tracking-wider">Branch Target</span>
                  <div className="flex items-center space-x-2 text-xs font-mono bg-[#FFFBEA] p-3 rounded-xl border border-[#DCD3A5]">
                    <GitBranch className="h-4 w-4 text-[#6D28D9]" />
                    <span className="text-[#6D28D9] font-bold">{activePr.branch_name}</span>
                    <span className="text-[#77735D]">merges into</span>
                    <span className="text-[#282719] font-bold">{activePr.base_branch}</span>
                  </div>
                </div>

                {/* Generated PR Description */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#77735D] uppercase tracking-wider">
                      Pull Request Description &amp; Verification Evidence
                    </span>
                    <span className="text-[11px] font-mono text-[#77735D]">Markdown Format</span>
                  </div>
                  <div className="rounded-xl bg-[#FFFBEA] p-4.5 border border-[#DCD3A5] font-mono text-xs text-[#282719] leading-relaxed overflow-x-auto max-h-96 whitespace-pre-wrap">
                    {activePr.body}
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
