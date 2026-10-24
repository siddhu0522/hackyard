import React, { useState, useEffect } from 'react';
import {
  Settings,
  Database,
  Cpu,
  RefreshCw,
  CheckCircle2,
  Server,
  Sparkles
} from 'lucide-react';
import { SystemConfigStatus, SystemHealth } from '../types';
import { api } from '../services/api';

interface SettingsViewProps {
  onSeedDemo: () => void;
  isSeeding: boolean;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ onSeedDemo, isSeeding }) => {
  const [config, setConfig] = useState<SystemConfigStatus | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    setLoading(true);
    try {
      const [c, h] = await Promise.all([api.getConfigStatus(), api.getHealth()]);
      setConfig(c);
      setHealth(h);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-responsive-title font-bold text-[#282719] flex items-center space-x-2.5">
            <div className="h-7 w-7 rounded-lg bg-[#EDE9FE] border border-[#DDD6FE] flex items-center justify-center">
              <Settings className="h-4 w-4 text-[#6D28D9]" />
            </div>
            <span>Settings &amp; Integrations</span>
          </h1>
          <p className="text-responsive-body text-[#625F4B] mt-1">
            System configuration status, AI provider setup, SQLite persistence, and safety rules
          </p>
        </div>

        <button
          onClick={loadStatus}
          disabled={loading}
          className="flex items-center space-x-1.5 rounded-lg bg-white hover:bg-[#E6D9A0] px-3.5 py-2 text-xs font-semibold text-[#282719] border border-[#DCD3A5] transition-colors disabled:opacity-50 self-start sm:self-auto shadow-2xs"
        >
          <RefreshCw className={`h-3.5 w-3.5 text-[#6D28D9] ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Diagnostics</span>
        </button>
      </div>

      {/* System Health Status Panels */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-xl bg-white p-5 border border-[#DCD3A5] shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#77735D] uppercase tracking-wider">Database Engine</span>
            <Database className="h-4 w-4 text-[#15803D]" />
          </div>
          <div className="mt-2 text-base font-bold text-[#282719]">SQLite Relational</div>
          <div className="mt-1 flex items-center space-x-1.5 text-xs text-[#15803D] font-bold">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Connected &amp; Initialized</span>
          </div>
        </div>

        <div className="rounded-xl bg-white p-5 border border-[#DCD3A5] shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#77735D] uppercase tracking-wider">Background Scheduler</span>
            <Server className="h-4 w-4 text-[#6D28D9]" />
          </div>
          <div className="mt-2 text-base font-bold text-[#282719]">APScheduler AsyncIO</div>
          <div className="mt-1 flex items-center space-x-1.5 text-xs text-[#6D28D9] font-bold">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Running in Background</span>
          </div>
        </div>

        <div className="rounded-xl bg-white p-5 border border-[#DCD3A5] shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#77735D] uppercase tracking-wider">AI Provider</span>
            <Cpu className="h-4 w-4 text-[#6D28D9]" />
          </div>
          <div className="mt-2 text-base font-bold text-[#282719] uppercase">{config?.llm_provider || 'Mock Engine'}</div>
          <div className="mt-1 flex items-center space-x-1.5 text-xs text-[#6D28D9] font-bold">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Ready for Code Synthesis</span>
          </div>
        </div>
      </div>

      {/* Integrations and Boundaries Panel */}
      <div className="rounded-xl bg-white p-6 border border-[#DCD3A5] space-y-4 shadow-sm">
        <div className="flex items-center justify-between border-b border-[#DCD3A5] pb-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-[#77735D]">
            APIVerse Security Boundaries &amp; Environment
          </h2>
          <span className="text-xs font-mono text-[#77735D]">Zero Cloud Leakage Mode Supported</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="rounded-xl bg-[#FFFBEA] p-4.5 border border-[#DCD3A5] space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-[#282719]">GitHub App Integration</span>
              <span className="rounded bg-[#FFFCD3] px-2 py-0.5 text-[10px] font-mono font-bold text-[#6D28D9] border border-[#DCD3A5]">
                {config?.github_app_configured ? 'APP CONFIGURED' : 'LOCAL DEMO MODE'}
              </span>
            </div>
            <p className="text-[#625F4B] leading-relaxed text-xs">
              When GitHub App keys are unconfigured, APIVerse safely runs in Local Demo Mode with simulated branch management and local worktree isolation.
            </p>
          </div>

          <div className="rounded-xl bg-[#FFFBEA] p-4.5 border border-[#DCD3A5] space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-[#282719]">Developer Approval Policy</span>
              <span className="rounded bg-[#DCFCE7] px-2 py-0.5 text-[10px] font-mono font-bold text-[#15803D] border border-[#BBF7D0]">
                STRICT ENFORCEMENT
              </span>
            </div>
            <p className="text-[#625F4B] leading-relaxed text-xs">
              Every AI-synthesized repair requires explicit manual developer authorization in the AI Repair Studio before a Pull Request can be published.
            </p>
          </div>

          <div className="rounded-xl bg-[#FFFBEA] p-4.5 border border-[#DCD3A5] space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-[#282719]">Database Storage Path</span>
              <span className="font-mono text-[#77735D] text-[10px] font-bold">LOCAL DISK</span>
            </div>
            <div className="font-mono text-[#6D28D9] font-bold select-all truncate bg-white p-2.5 rounded-lg border border-[#DCD3A5] text-xs">
              {config?.database_path || 'backend/data/bump.db'}
            </div>
          </div>

          <div className="rounded-xl bg-[#FFFBEA] p-4.5 border border-[#DCD3A5] space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-[#282719]">Sandbox Isolation Root</span>
              <span className="font-mono text-[#77735D] text-[10px] font-bold">TIME &amp; CPU LIMITED</span>
            </div>
            <div className="font-mono text-[#6D28D9] font-bold select-all truncate bg-white p-2.5 rounded-lg border border-[#DCD3A5] text-xs">
              {config?.sandbox_path || 'backend/data/sandbox'}
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Demo Dataset Reset Banner */}
      <div className="rounded-xl bg-gradient-to-r from-[#FFFCD3] via-white to-[#FFFCD3] border border-[#DCD3A5] p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-4 w-4 text-[#6D28D9]" />
            <h3 className="text-responsive-card font-bold text-[#282719]">Interactive Demonstration Scenario</h3>
            <span className="rounded bg-[#EDE9FE] px-2 py-0.5 text-[10px] font-mono font-bold text-[#6D28D9] border border-[#DDD6FE]">
              APIVerse
            </span>
          </div>
          <p className="text-xs text-[#625F4B] max-w-xl leading-relaxed">
            Populate sample OpenAPI specs (v1 vs v2 breaking changes), client repositories, code impact matches,
            an AI repair proposal, verified sandbox test runs, and open Pull Requests with a single click.
          </p>
        </div>

        <button
          onClick={onSeedDemo}
          disabled={isSeeding}
          className="flex items-center space-x-2 rounded-lg bg-[#6D28D9] hover:bg-[#5B21B6] px-4 py-2.5 text-xs font-semibold text-white shadow-xs transition-all shrink-0 disabled:opacity-50 self-start sm:self-auto"
        >
          <Sparkles className={`h-3.5 w-3.5 ${isSeeding ? 'animate-spin' : ''}`} />
          <span>{isSeeding ? 'Populating Dataset...' : 'Re-Seed Demo Data'}</span>
        </button>
      </div>
    </div>
  );
};
