import React, { useState } from 'react';
import {
  LocateFixed,
  FileCode2,
  Wrench,
  ArrowRight
} from 'lucide-react';
import { AffectedFile, DetectedChange } from '../types';

interface CodeImpactViewProps {
  selectedChange: DetectedChange | null;
  affectedFiles: AffectedFile[];
  onTriggerRepair: (change: DetectedChange) => void;
}

export const CodeImpactView: React.FC<CodeImpactViewProps> = ({
  selectedChange,
  affectedFiles,
  onTriggerRepair,
}) => {
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null);

  if (!selectedChange) {
    return (
      <div className="apv-panel p-12 text-center text-xs text-[#77735D]">
        No active breaking change selected. Go to Breaking Changes tab and click &quot;Map Code Impact&quot;.
      </div>
    );
  }

  const activeFile = affectedFiles.find(f => f.id === selectedFileId) || affectedFiles[0];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-responsive-title font-bold text-[#282719] tracking-tight flex items-center space-x-2.5">
            <LocateFixed className="h-5 w-5 text-[#6D28D9]" />
            <span>Source Code Impact Analysis</span>
          </h1>
          <p className="text-responsive-body text-[#625F4B] mt-1">
            Deterministic AST and pattern matching connecting API breaking change to client repository code
          </p>
        </div>

        <button
          onClick={() => onTriggerRepair(selectedChange)}
          className="flex items-center space-x-1.5 rounded-lg bg-[#6D28D9] hover:bg-[#5B21B6] px-4 py-2 text-xs font-semibold text-white shadow-xs transition-all self-start sm:self-auto"
        >
          <Wrench className="h-3.5 w-3.5" />
          <span>Launch AI Repair Studio</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Target Change Context Bar */}
      <div className="rounded-xl bg-[#FFFCD3] border border-[#DCD3A5] p-3.5 flex items-center justify-between shadow-2xs">
        <div className="flex items-center space-x-2.5 text-xs truncate">
          <span className="rounded bg-[#FEE2E2] px-2 py-0.5 text-[10px] font-bold text-[#DC2626] border border-[#FECACA] shrink-0">
            {selectedChange.change_type}
          </span>
          <span className="font-mono text-[#282719] font-bold shrink-0">
            {selectedChange.http_method || 'ANY'} {selectedChange.path}
          </span>
          <span className="text-[#625F4B] truncate hidden md:inline">{selectedChange.description}</span>
        </div>
      </div>

      {affectedFiles.length === 0 ? (
        <div className="apv-panel p-12 text-center text-xs text-[#77735D]">
          No client source files impacted by this specific change in the repository.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Affected Locations List (5 cols) */}
          <div className="lg:col-span-5 space-y-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#77735D] px-1">
              Impacted Locations ({affectedFiles.length})
            </h2>

            {affectedFiles.map(file => {
              const isSelected = activeFile?.id === file.id;
              const isConfirmed = file.match_confidence === 'confirmed';
              return (
                <div
                  key={file.id}
                  onClick={() => setSelectedFileId(file.id)}
                  className={`apv-panel p-4 cursor-pointer transition-all border ${
                    isSelected
                      ? 'border-[#6D28D9] bg-[#FFFCD3] border-l-4 shadow-xs'
                      : 'border-[#DCD3A5] hover:border-[#C4B982] hover:bg-[#FFFCD3]/30'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs font-bold text-[#282719] flex items-center space-x-1.5 truncate">
                      <FileCode2 className="h-4 w-4 text-[#6D28D9] shrink-0" />
                      <span className="truncate">{file.file_path}</span>
                    </span>
                    <span
                      className={`rounded px-2 py-0.5 text-[10px] font-bold border shrink-0 ${
                        isConfirmed
                          ? 'bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]'
                          : 'bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]'
                      }`}
                    >
                      {file.match_confidence.toUpperCase()}
                    </span>
                  </div>

                  <div className="flex items-center space-x-2 text-xs text-[#625F4B] font-mono">
                    <span>Function: <strong className="text-[#282719] font-bold">{file.function_name}</strong></span>
                    <span>•</span>
                    <span>Lines {file.line_start}–{file.line_end}</span>
                  </div>

                  {file.context_reason && (
                    <p className="text-xs text-[#625F4B] mt-2 bg-[#FFFBEA] p-2.5 rounded-lg border border-[#DCD3A5] leading-relaxed">
                      {file.context_reason}
                    </p>
                  )}
                </div>
              );
            })}
          </div>

          {/* Source Code Evidence (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#77735D] px-1">
              Source Code Evidence
            </h2>

            {activeFile ? (
              <div className="apv-panel p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-[#DCD3A5] pb-3">
                  <div>
                    <span className="font-mono text-xs text-[#282719] font-bold">{activeFile.file_path}</span>
                    <span className="text-[11px] text-[#77735D] block font-mono mt-0.5">
                      Scope: {activeFile.function_name} (lines {activeFile.line_start} to {activeFile.line_end})
                    </span>
                  </div>
                  <span className="rounded bg-[#FFFCD3] px-2 py-0.5 text-xs text-[#6D28D9] font-mono font-bold border border-[#DCD3A5]">
                    {activeFile.language}
                  </span>
                </div>

                <div className="rounded-xl bg-[#FFFBEA] p-4 border border-[#DCD3A5] overflow-x-auto shadow-2xs">
                  <pre className="font-mono text-xs text-[#282719] leading-relaxed">
                    {activeFile.snippet}
                  </pre>
                </div>

                <div className="flex justify-end pt-1">
                  <button
                    onClick={() => onTriggerRepair(selectedChange)}
                    className="flex items-center space-x-1.5 rounded-lg bg-[#6D28D9] hover:bg-[#5B21B6] px-4 py-2 text-xs font-semibold text-white shadow-xs transition-all"
                  >
                    <span>Generate AI Patch for this File</span>
                    <ArrowRight className="h-3 w-3" />
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
