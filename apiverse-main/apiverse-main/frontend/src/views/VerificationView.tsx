import React, { useState, useEffect } from 'react';
import {
  Terminal,
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldAlert,
  ArrowRight,
  GitPullRequest,
  Command
} from 'lucide-react';
import { RepairAttempt, TestRun } from '../types';
import { api } from '../services/api';

interface VerificationViewProps {
  selectedRepair: RepairAttempt | null;
  onGoToPR: (repair: RepairAttempt) => void;
}

export const VerificationView: React.FC<VerificationViewProps> = ({
  selectedRepair,
  onGoToPR,
}) => {
  const [testRuns, setTestRuns] = useState<TestRun[]>([]);
  const [activeRun, setActiveRun] = useState<TestRun | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [customCommand, setCustomCommand] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (selectedRepair) {
      loadRuns(selectedRepair.id);
    }
  }, [selectedRepair]);

  const loadRuns = async (repairId: number) => {
    try {
      const runs = await api.getRunsByRepair(repairId);
      setTestRuns(runs);
      if (runs.length > 0) {
        setActiveRun(runs[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleExecuteVerification = async () => {
    if (!selectedRepair) return;
    setIsRunning(true);
    setErrorMsg(null);
    try {
      const run = await api.runVerification(selectedRepair.id, customCommand || undefined);
      await loadRuns(selectedRepair.id);
      setActiveRun(run);
    } catch (err: any) {
      setErrorMsg(err.message || 'Verification execution failed.');
    } finally {
      setIsRunning(false);
    }
  };

  if (!selectedRepair) {
    return (
      <div className="rounded-xl border border-[#DCD3A5] bg-white p-12 text-center text-xs text-[#77735D]">
        <Terminal className="h-8 w-8 text-[#77735D] mx-auto mb-3" />
        <p className="text-[#282719] font-bold text-sm">No repair attempt selected</p>
        <p className="text-[#625F4B] mt-1">Navigate to AI Repair Studio to generate a repair patch before running isolated verification.</p>
      </div>
    );
  }

  const isVerified = activeRun?.status === 'passed';
  const canPublishPR = isVerified && selectedRepair.developer_approved;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-responsive-title font-bold text-[#282719] flex items-center space-x-2.5">
            <div className="h-7 w-7 rounded-lg bg-[#DCFCE7] border border-[#BBF7D0] flex items-center justify-center">
              <Terminal className="h-4 w-4 text-[#15803D]" />
            </div>
            <span>Test Verification</span>
          </h1>
          <p className="text-responsive-body text-[#625F4B] mt-1">
            Validates proposed code repairs against repository tests in isolated sandbox worktrees
          </p>
        </div>

        {canPublishPR && (
          <button
            onClick={() => onGoToPR(selectedRepair)}
            className="flex items-center space-x-2 rounded-lg bg-[#6D28D9] hover:bg-[#5B21B6] px-4 py-2 text-xs font-semibold text-white shadow-xs transition-all self-start sm:self-auto"
          >
            <GitPullRequest className="h-3.5 w-3.5" />
            <span>Open Verified Pull Request</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* Target Repair Header Bar */}
      <div className="rounded-xl bg-white border border-[#DCD3A5] p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs">
        <div className="flex items-center flex-wrap gap-2 text-xs text-[#625F4B]">
          <span className="font-mono font-bold text-[#6D28D9]">Repair #{selectedRepair.id}</span>
          <span className="text-[#77735D]">•</span>
          <span>Patches: <strong className="text-[#282719]">{selectedRepair.patches?.length || 0} file(s)</strong></span>
          <span className="text-[#77735D]">•</span>
          <span>
            Approval:{' '}
            <strong className={selectedRepair.developer_approved ? 'text-[#15803D]' : 'text-[#B45309]'}>
              {selectedRepair.developer_approved ? 'Approved' : 'Pending Authorization'}
            </strong>
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <div className="relative">
            <Command className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-[#77735D]" />
            <input
              type="text"
              placeholder="Command (e.g. pytest)"
              value={customCommand}
              onChange={e => setCustomCommand(e.target.value)}
              className="rounded-lg bg-white border border-[#DCD3A5] pl-7 pr-3 py-1.5 text-xs text-[#282719] placeholder-[#77735D] focus:outline-none focus:border-[#6D28D9] w-48 sm:w-56 font-mono"
            />
          </div>
          <button
            onClick={handleExecuteVerification}
            disabled={isRunning}
            className="flex items-center space-x-1.5 rounded-lg bg-[#15803D] hover:bg-[#166534] px-3.5 py-1.5 text-xs font-semibold text-white transition-colors disabled:opacity-50 shadow-xs"
          >
            <Play className={`h-3 w-3 ${isRunning ? 'animate-spin' : ''}`} />
            <span>{isRunning ? 'Running in Sandbox...' : 'Run Tests'}</span>
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="rounded-xl bg-[#FEE2E2] border border-[#FECACA] p-4 text-xs font-semibold text-[#DC2626]">
          {errorMsg}
        </div>
      )}

      {/* Safety Policy Notice */}
      {!selectedRepair.developer_approved && (
        <div className="rounded-xl bg-[#FEF3C7] border border-[#FDE68A] p-4 flex items-center space-x-3 text-xs text-[#B45309]">
          <ShieldAlert className="h-5 w-5 shrink-0 text-[#B45309]" />
          <div>
            <strong className="font-bold text-[#282719]">Developer Approval Boundary Active: </strong>
            <span>
              Even if sandbox tests pass, automated Pull Request publication requires explicit developer authorization in the AI Repair Studio.
            </span>
          </div>
        </div>
      )}

      {/* Active Run Results */}
      {activeRun ? (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="rounded-xl bg-white p-4 border border-[#DCD3A5] shadow-2xs">
              <span className="text-[#77735D] text-[10px] font-bold uppercase tracking-wider">Execution Status</span>
              <div className="mt-1.5 flex items-center space-x-2">
                {activeRun.status === 'passed' ? (
                  <CheckCircle2 className="h-4 w-4 text-[#15803D]" />
                ) : (
                  <XCircle className="h-4 w-4 text-[#DC2626]" />
                )}
                <span className={`text-sm font-bold uppercase ${
                  activeRun.status === 'passed' ? 'text-[#15803D]' : 'text-[#DC2626]'
                }`}>
                  {activeRun.status}
                </span>
              </div>
            </div>

            <div className="rounded-xl bg-white p-4 border border-[#DCD3A5] shadow-2xs">
              <span className="text-[#77735D] text-[10px] font-bold uppercase tracking-wider">Test Suite Command</span>
              <div className="mt-1.5 font-mono text-xs text-[#6D28D9] font-bold truncate">
                {activeRun.command || 'pytest tests/'}
              </div>
            </div>

            <div className="rounded-xl bg-white p-4 border border-[#DCD3A5] shadow-2xs">
              <span className="text-[#77735D] text-[10px] font-bold uppercase tracking-wider">Test Results</span>
              <div className="mt-1.5 text-xs text-[#282719] font-mono">
                <span className="text-[#15803D] font-bold">{activeRun.passed_tests} passed</span>
                {activeRun.failed_tests > 0 && (
                  <span className="text-[#DC2626] font-bold ml-2">{activeRun.failed_tests} failed</span>
                )}
              </div>
            </div>

            <div className="rounded-xl bg-white p-4 border border-[#DCD3A5] shadow-2xs">
              <span className="text-[#77735D] text-[10px] font-bold uppercase tracking-wider">Execution Duration</span>
              <div className="mt-1.5 flex items-center space-x-1.5 text-xs text-[#282719] font-mono">
                <Clock className="h-3.5 w-3.5 text-[#77735D]" />
                <span>{activeRun.duration_seconds}s</span>
              </div>
            </div>
          </div>

          {/* Sandbox Terminal Console */}
          <div className="rounded-xl bg-white border border-[#DCD3A5] overflow-hidden shadow-sm">
            <div className="flex items-center justify-between bg-[#FFFCD3] px-4 py-2.5 border-b border-[#DCD3A5]">
              <div className="flex items-center space-x-2">
                <div className="h-2.5 w-2.5 rounded-full bg-[#DC2626]"></div>
                <div className="h-2.5 w-2.5 rounded-full bg-[#B45309]"></div>
                <div className="h-2.5 w-2.5 rounded-full bg-[#15803D]"></div>
                <span className="ml-2 font-mono text-xs text-[#282719] font-semibold">Isolated Sandbox Terminal Output</span>
              </div>
              <span className="text-[11px] text-[#77735D] font-mono bg-white px-2 py-0.5 rounded border border-[#DCD3A5]">Exit Code: {activeRun.exit_code}</span>
            </div>

            <div className="p-4 font-mono text-xs text-[#282719] bg-[#FFFBEA] leading-relaxed overflow-x-auto max-h-96">
              {activeRun.stdout ? (
                <pre className="whitespace-pre-wrap">{activeRun.stdout}</pre>
              ) : (
                <span className="text-[#77735D]">No standard output recorded.</span>
              )}

              {activeRun.stderr && (
                <pre className="mt-3 text-[#DC2626] font-bold whitespace-pre-wrap">{activeRun.stderr}</pre>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-[#DCD3A5] bg-white p-12 text-center text-xs text-[#77735D]">
          No test execution runs recorded yet. Click &quot;Run Tests&quot; above to execute sandbox verification.
        </div>
      )}
    </div>
  );
};
