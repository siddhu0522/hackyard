import React, { useState, useEffect } from 'react';
import {
  Wrench,
  Sparkles,
  CheckCircle2,
  ShieldCheck,
  Play,
  FileCode2,
  AlertTriangle,
  Edit3
} from 'lucide-react';
import { DetectedChange, RepairAttempt, ProposedPatch } from '../types';
import { api } from '../services/api';

interface RepairStudioViewProps {
  selectedChange: DetectedChange | null;
  onGoToVerification: (repair: RepairAttempt) => void;
}

export const RepairStudioView: React.FC<RepairStudioViewProps> = ({
  selectedChange,
  onGoToVerification,
}) => {
  const [repairs, setRepairs] = useState<RepairAttempt[]>([]);
  const [activeRepair, setActiveRepair] = useState<RepairAttempt | null>(null);
  const [activePatch, setActivePatch] = useState<ProposedPatch | null>(null);
  const [provider, setProvider] = useState('mock');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedCode, setEditedCode] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (selectedChange) {
      loadRepairs(selectedChange.id);
    }
  }, [selectedChange]);

  const loadRepairs = async (changeId: number) => {
    try {
      const res = await api.getRepairsByChange(changeId);
      setRepairs(res);
      if (res.length > 0) {
        setActiveRepair(res[0]);
        if (res[0].patches && res[0].patches.length > 0) {
          setActivePatch(res[0].patches[0]);
          setEditedCode(res[0].patches[0].patched_content);
        }
      } else {
        setActiveRepair(null);
        setActivePatch(null);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleGenerate = async () => {
    if (!selectedChange) return;
    setIsGenerating(true);
    setErrorMsg(null);
    try {
      const newRepair = await api.generateRepair(selectedChange.id, provider);
      await loadRepairs(selectedChange.id);
      setActiveRepair(newRepair);
      if (newRepair.patches && newRepair.patches.length > 0) {
        setActivePatch(newRepair.patches[0]);
        setEditedCode(newRepair.patches[0].patched_content);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to generate repair.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApproval = async (approved: boolean) => {
    if (!activeRepair) return;
    setIsApproving(true);
    try {
      const updated = await api.approveRepair(activeRepair.id, approved);
      setActiveRepair(updated);
    } catch (err: any) {
      alert(`Approval error: ${err.message}`);
    } finally {
      setIsApproving(false);
    }
  };

  const handleSavePatchEdit = async () => {
    if (!activePatch) return;
    try {
      const updatedPatch = await api.updatePatch(activePatch.id, editedCode);
      setActivePatch(updatedPatch);
      setIsEditing(false);
      if (activeRepair) {
        await loadRepairs(activeRepair.detected_change_id);
      }
    } catch (err: any) {
      alert(`Failed to save patch: ${err.message}`);
    }
  };

  if (!selectedChange) {
    return (
      <div className="apv-panel p-12 text-center text-xs text-[#77735D]">
        No active breaking change selected. Go to Breaking Changes tab to pick a change.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-responsive-title font-bold text-[#282719] tracking-tight flex items-center space-x-2.5">
            <Wrench className="h-5 w-5 text-[#6D28D9]" />
            <span>AI Repair Studio</span>
          </h1>
          <p className="text-responsive-body text-[#625F4B] mt-1">
            Automated code repair generation, unified diff inspection, and developer approval controls
          </p>
        </div>

        {activeRepair && (
          <button
            onClick={() => onGoToVerification(activeRepair)}
            className="flex items-center space-x-1.5 rounded-lg bg-[#15803D] hover:bg-[#166534] px-4 py-2 text-xs font-semibold text-white shadow-xs transition-all self-start sm:self-auto"
          >
            <Play className="h-3 w-3 fill-current" />
            <span>Execute Test Verification</span>
          </button>
        )}
      </div>

      {/* Target Change Context */}
      <div className="rounded-xl bg-[#FFFCD3] border border-[#DCD3A5] p-3.5 flex items-center justify-between text-xs shadow-2xs">
        <div className="flex items-center space-x-2.5 truncate">
          <span className="rounded bg-[#FEE2E2] px-2 py-0.5 text-[10px] font-bold text-[#DC2626] border border-[#FECACA] shrink-0">
            {selectedChange.change_type}
          </span>
          <span className="font-mono text-[#282719] font-bold shrink-0">
            {selectedChange.http_method || 'ANY'} {selectedChange.path}
          </span>
          <span className="text-[#625F4B] truncate hidden md:inline">{selectedChange.description}</span>
        </div>
      </div>

      {/* Synthesis Toolbar */}
      <div className="apv-panel p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-2.5 text-xs">
          <span className="text-[#625F4B] font-bold">Model Engine:</span>
          <select
            value={provider}
            onChange={e => setProvider(e.target.value)}
            className="rounded-lg bg-white border border-[#DCD3A5] px-3 py-1.5 text-xs text-[#282719] focus:outline-none focus:border-[#6D28D9] focus:ring-1 focus:ring-[#6D28D9]"
          >
            <option value="mock">Deterministic Rule Engine (Local / Offline)</option>
            <option value="openai">OpenAI GPT-4o (Server Key)</option>
            <option value="anthropic">Anthropic Claude 3.5 Sonnet</option>
            <option value="gemini">Google Gemini 1.5 Pro</option>
          </select>
        </div>

        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="flex items-center space-x-1.5 rounded-lg bg-[#6D28D9] hover:bg-[#5B21B6] px-4 py-2 text-xs font-semibold text-white shadow-xs transition-all disabled:opacity-50"
        >
          <Sparkles className={`h-3.5 w-3.5 ${isGenerating ? 'animate-spin' : ''}`} />
          <span>{isGenerating ? 'Synthesizing Patch...' : 'Synthesize AI Repair'}</span>
        </button>
      </div>

      {errorMsg && (
        <div className="rounded-xl bg-[#FEE2E2] border border-[#FECACA] p-3 text-xs font-semibold text-[#DC2626]">
          {errorMsg}
        </div>
      )}

      {/* Repair Content Details */}
      {activeRepair ? (
        <div className="space-y-6">
          {/* Explanation & Approval Control */}
          <div className="apv-panel p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#DCD3A5] pb-3.5 gap-3">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold text-[#6D28D9]">Repair #{activeRepair.id}</span>
                  <span className="rounded bg-[#FFFCD3] px-2 py-0.5 text-[10px] text-[#282719] font-mono border border-[#DCD3A5]">
                    {activeRepair.model_name}
                  </span>
                </div>
                <h3 className="text-responsive-card font-bold text-[#282719] mt-1">Proposed Code Resolution</h3>
              </div>

              {/* Developer Approval Guard */}
              <div className="flex flex-wrap items-center gap-2.5">
                {activeRepair.developer_approved ? (
                  <span className="flex items-center space-x-1.5 rounded-full bg-[#DCFCE7] px-3 py-1 text-xs font-bold text-[#15803D] border border-[#BBF7D0]">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Approved by Developer</span>
                  </span>
                ) : (
                  <span className="flex items-center space-x-1.5 rounded-full bg-[#FEF3C7] px-3 py-1 text-xs font-bold text-[#B45309] border border-[#FDE68A]">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    <span>Awaiting Developer Approval</span>
                  </span>
                )}

                <button
                  onClick={() => handleApproval(!activeRepair.developer_approved)}
                  disabled={isApproving}
                  className={`rounded-lg px-3.5 py-1.5 text-xs font-bold transition-all ${
                    activeRepair.developer_approved
                      ? 'bg-white text-[#282719] hover:bg-[#E6D9A0] border border-[#DCD3A5]'
                      : 'bg-[#15803D] text-white hover:bg-[#166534] shadow-xs'
                  }`}
                >
                  {activeRepair.developer_approved ? 'Revoke Approval' : 'Authorize Fix'}
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-xs font-bold text-[#77735D] uppercase tracking-wider">Failure Explanation</span>
                <p className="mt-1.5 text-[#282719] bg-[#FFFBEA] p-3.5 rounded-xl border border-[#DCD3A5] leading-relaxed">
                  {activeRepair.explanation}
                </p>
              </div>
              <div>
                <span className="text-xs font-bold text-[#77735D] uppercase tracking-wider">Repair Reasoning</span>
                <p className="mt-1.5 text-[#282719] bg-[#FFFBEA] p-3.5 rounded-xl border border-[#DCD3A5] leading-relaxed">
                  {activeRepair.reasoning}
                </p>
              </div>
            </div>

            {activeRepair.known_risks && (
              <div className="rounded-xl bg-[#FEF3C7] border border-[#FDE68A] p-3 text-xs text-[#B45309] flex items-start space-x-2.5">
                <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Risk Assessment: </span>
                  <span>{activeRepair.known_risks}</span>
                </div>
              </div>
            )}
          </div>

          {/* Unified Diff & Patch Editor */}
          {activePatch && (
            <div className="apv-panel p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#DCD3A5] pb-3">
                <div className="flex items-center space-x-2 font-mono text-xs">
                  <FileCode2 className="h-4 w-4 text-[#6D28D9]" />
                  <span className="font-bold text-[#282719]">{activePatch.file_path}</span>
                  <span className="rounded bg-[#DCFCE7] px-2 py-0.5 text-[10px] text-[#15803D] font-bold border border-[#BBF7D0]">
                    Syntax Valid
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className="flex items-center space-x-1.5 rounded-lg bg-white px-3 py-1.5 text-xs text-[#282719] hover:bg-[#E6D9A0] border border-[#DCD3A5] font-semibold transition-colors"
                  >
                    <Edit3 className="h-3.5 w-3.5" />
                    <span>{isEditing ? 'View Diff' : 'Edit Patch'}</span>
                  </button>
                  {isEditing && (
                    <button
                      onClick={handleSavePatchEdit}
                      className="rounded-lg bg-[#6D28D9] px-3.5 py-1.5 text-xs font-bold text-white hover:bg-[#5B21B6] shadow-xs"
                    >
                      Save
                    </button>
                  )}
                </div>
              </div>

              {isEditing ? (
                <textarea
                  rows={10}
                  value={editedCode}
                  onChange={e => setEditedCode(e.target.value)}
                  className="w-full rounded-xl bg-[#FFFBEA] p-4 font-mono text-xs text-[#282719] border border-[#DCD3A5] leading-relaxed focus:outline-none focus:border-[#6D28D9]"
                />
              ) : (
                <div className="rounded-xl bg-[#FFFBEA] p-4 border border-[#DCD3A5] overflow-x-auto shadow-2xs">
                  <pre className="font-mono text-xs leading-relaxed">
                    {activePatch.unified_diff.split('\n').map((line, idx) => {
                      let color = 'text-[#282719]';
                      let bg = 'transparent';
                      if (line.startsWith('+') && !line.startsWith('+++')) {
                        color = 'text-[#15803D] font-bold';
                        bg = 'bg-[#DCFCE7]';
                      } else if (line.startsWith('-') && !line.startsWith('---')) {
                        color = 'text-[#DC2626] font-bold';
                        bg = 'bg-[#FEE2E2]';
                      } else if (line.startsWith('@@')) {
                        color = 'text-[#6D28D9] font-bold';
                        bg = 'bg-[#EDE9FE]';
                      }
                      return (
                        <div key={idx} className={`${bg} px-2 py-0.5 rounded-sm ${color}`}>
                          {line}
                        </div>
                      );
                    })}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="apv-panel p-12 text-center text-xs text-[#77735D]">
          No repair proposals generated yet. Click &quot;Synthesize AI Repair&quot; above.
        </div>
      )}
    </div>
  );
};
