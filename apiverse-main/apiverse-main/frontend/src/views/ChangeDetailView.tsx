import React, { useState } from 'react';
import {
  AlertTriangle,
  Layers,
  FileCheck2,
  Filter,
  ChevronRight
} from 'lucide-react';
import { DetectedChange, ScanDetail } from '../types';

interface ChangeDetailViewProps {
  scans: ScanDetail[];
  selectedScanId: number | null;
  onSelectScan: (id: number) => void;
  onAnalyzeImpact: (change: DetectedChange) => void;
  onGoToRepair: (change: DetectedChange) => void;
}

export const ChangeDetailView: React.FC<ChangeDetailViewProps> = ({
  scans,
  selectedScanId,
  onSelectScan,
  onAnalyzeImpact,
  onGoToRepair,
}) => {
  const [filterSeverity, setFilterSeverity] = useState<'ALL' | 'BREAKING' | 'WARNING' | 'INFO'>('ALL');
  const [selectedChangeId, setSelectedChangeId] = useState<number | null>(null);

  const activeScan = scans.find(s => s.id === selectedScanId) || scans[0];
  const changes = activeScan?.detected_changes || [];

  const filteredChanges = changes.filter(c => {
    if (filterSeverity === 'ALL') return true;
    return c.severity === filterSeverity;
  });

  const selectedChange = changes.find(c => c.id === selectedChangeId) || filteredChanges[0];

  const parseEvidence = (evidenceStr: string) => {
    try {
      return JSON.parse(evidenceStr);
    } catch (_) {
      return {};
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-responsive-title font-bold text-[#282719] tracking-tight flex items-center space-x-2.5">
            <AlertTriangle className="h-5 w-5 text-[#DC2626]" />
            <span>Breaking Changes &amp; Evidence Inspector</span>
          </h1>
          <p className="text-responsive-body text-[#625F4B] mt-1">
            Deterministic rule-based change classification with exact JSON-pointer evidence
          </p>
        </div>

        {/* Scan Picker */}
        {scans.length > 0 && (
          <div className="flex items-center space-x-2 self-start sm:self-auto">
            <span className="text-xs text-[#625F4B] font-bold">Scan:</span>
            <select
              value={activeScan?.id}
              onChange={e => onSelectScan(Number(e.target.value))}
              className="rounded-lg bg-white border border-[#DCD3A5] px-3 py-1.5 text-xs text-[#282719] focus:outline-none focus:border-[#6D28D9] focus:ring-1 focus:ring-[#6D28D9]"
            >
              {scans.map(s => (
                <option key={s.id} value={s.id}>
                  Scan #{s.id} ({s.breaking_changes} breaking)
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-[#625F4B] flex items-center space-x-1 mr-1 font-semibold">
          <Filter className="h-3.5 w-3.5 text-[#77735D]" />
          <span>Severity:</span>
        </span>
        {(['ALL', 'BREAKING', 'WARNING', 'INFO'] as const).map(sev => (
          <button
            key={sev}
            onClick={() => setFilterSeverity(sev)}
            className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-all ${
              filterSeverity === sev
                ? 'bg-[#6D28D9] text-white shadow-xs'
                : 'bg-white text-[#625F4B] hover:text-[#282719] hover:bg-[#E6D9A0] border border-[#DCD3A5]'
            }`}
          >
            {sev}
          </button>
        ))}
      </div>

      {filteredChanges.length === 0 ? (
        <div className="apv-panel p-12 text-center text-xs text-[#77735D]">
          No detected changes matching filter in this scan.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Change List Table / Cards (5 cols) */}
          <div className="lg:col-span-5 space-y-3">
            {filteredChanges.map(c => {
              const isSelected = selectedChange?.id === c.id;
              const isBreaking = c.severity === 'BREAKING';
              return (
                <div
                  key={c.id}
                  onClick={() => setSelectedChangeId(c.id)}
                  className={`apv-panel p-4 cursor-pointer transition-all border ${
                    isSelected
                      ? 'border-[#6D28D9] bg-[#FFFCD3] border-l-4 shadow-xs'
                      : 'border-[#DCD3A5] hover:border-[#C4B982] hover:bg-[#FFFCD3]/30'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`rounded px-2 py-0.5 text-[10px] font-bold border ${
                        isBreaking
                          ? 'bg-[#FEE2E2] text-[#DC2626] border-[#FECACA]'
                          : c.severity === 'WARNING'
                          ? 'bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]'
                          : 'bg-[#EDE9FE] text-[#6D28D9] border-[#DDD6FE]'
                      }`}
                    >
                      {c.severity}
                    </span>
                    <span className="font-mono text-xs text-[#77735D]">{c.rule_code}</span>
                  </div>

                  <div className="flex items-center space-x-2 font-mono text-xs text-[#282719] font-bold truncate">
                    {c.http_method && (
                      <span className="rounded bg-[#FFFCD3] px-1.5 py-0.5 text-[10px] text-[#6D28D9] font-bold border border-[#DCD3A5]">
                        {c.http_method}
                      </span>
                    )}
                    <span className="truncate">{c.path}</span>
                  </div>

                  <p className="text-xs text-[#625F4B] mt-2 line-clamp-2 leading-relaxed">
                    {c.description}
                  </p>

                  <div className="mt-3 flex items-center justify-between pt-2 border-t border-[#DCD3A5]/60 text-[11px] text-[#77735D] font-mono">
                    <span>Status: {c.status}</span>
                    <ChevronRight className="h-4 w-4 text-[#77735D]" />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Evidence Details Panel (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            {selectedChange ? (
              <div className="apv-panel p-5 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#DCD3A5] pb-3 gap-3">
                  <div>
                    <span className="text-[10px] font-mono text-[#6D28D9] uppercase font-bold tracking-wider">
                      Rule Code: {selectedChange.rule_code}
                    </span>
                    <h2 className="text-responsive-card font-bold text-[#282719] mt-0.5">
                      {selectedChange.change_type}
                    </h2>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => onAnalyzeImpact(selectedChange)}
                      className="flex items-center space-x-1.5 rounded-lg bg-[#6D28D9] hover:bg-[#5B21B6] px-3.5 py-2 text-xs font-semibold text-white shadow-xs transition-all"
                    >
                      <Layers className="h-3.5 w-3.5" />
                      <span>Map Code Impact</span>
                    </button>
                    {selectedChange.status !== 'detected' && (
                      <button
                        onClick={() => onGoToRepair(selectedChange)}
                        className="flex items-center space-x-1.5 rounded-lg bg-white hover:bg-[#E6D9A0] px-3.5 py-2 text-xs font-semibold text-[#282719] border border-[#DCD3A5] transition-colors"
                      >
                        <FileCheck2 className="h-3.5 w-3.5 text-[#6D28D9]" />
                        <span>AI Studio</span>
                      </button>
                    )}
                  </div>
                </div>

                <div className="space-y-4 text-xs">
                  <div>
                    <h3 className="text-xs font-bold text-[#77735D] uppercase tracking-wider">Description</h3>
                    <p className="text-[#282719] mt-1.5 bg-[#FFFBEA] p-3.5 rounded-xl border border-[#DCD3A5] leading-relaxed">
                      {selectedChange.description}
                    </p>
                  </div>

                  {(() => {
                    const ev = parseEvidence(selectedChange.evidence_json);
                    return (
                      <div className="space-y-4">
                        <div>
                          <h3 className="text-xs font-bold text-[#77735D] uppercase tracking-wider">JSON-Pointer Target Path</h3>
                          <div className="mt-1.5 rounded-xl bg-[#FFFCD3] p-3 font-mono text-xs text-[#6D28D9] font-bold border border-[#DCD3A5] select-all">
                            {ev.json_pointer || `/paths${selectedChange.path}`}
                          </div>
                        </div>

                        <div>
                          <h3 className="text-xs font-bold text-[#77735D] uppercase tracking-wider">Rule Rationale &amp; Evidence</h3>
                          <p className="mt-1.5 text-[#282719] bg-[#FFFBEA] p-3.5 rounded-xl border border-[#DCD3A5] leading-relaxed">
                            {ev.explanation || 'Detected via standard OpenAPI backward compatibility rules.'}
                          </p>
                        </div>

                        {selectedChange.old_value && (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <h3 className="text-xs font-bold text-[#77735D] uppercase tracking-wider">Base Specification</h3>
                              <pre className="mt-1.5 rounded-xl bg-[#FFFBEA] p-3 text-xs font-mono text-[#282719] border border-[#DCD3A5] overflow-x-auto leading-relaxed">
                                {selectedChange.old_value}
                              </pre>
                            </div>
                            <div>
                              <h3 className="text-xs font-bold text-[#77735D] uppercase tracking-wider">Target Specification</h3>
                              <pre className="mt-1.5 rounded-xl bg-[#FFFBEA] p-3 text-xs font-mono text-[#282719] border border-[#DCD3A5] overflow-x-auto leading-relaxed">
                                {selectedChange.new_value || '(Removed)'}
                              </pre>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })()}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
