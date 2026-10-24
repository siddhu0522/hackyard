import React, { useState } from 'react';
import {
  FileCode2,
  Play,
  AlertTriangle,
  Clock,
  ArrowRight,
  Plus,
  X
} from 'lucide-react';
import { ApiSpecification, Repository, ScanDetail } from '../types';
import { api } from '../services/api';

interface SpecsAndScansViewProps {
  specifications: ApiSpecification[];
  repositories: Repository[];
  scans: ScanDetail[];
  onScanCreated: (newScan: ScanDetail) => void;
  onRefresh: () => void;
  onInspectScan: (scanId: number) => void;
}

export const SpecsAndScansView: React.FC<SpecsAndScansViewProps> = ({
  specifications,
  repositories,
  scans,
  onScanCreated,
  onRefresh,
  onInspectScan,
}) => {
  const [prevSpecId, setPrevSpecId] = useState<number | ''>('');
  const [currSpecId, setCurrSpecId] = useState<number | ''>('');
  const [repoId, setRepoId] = useState<number | ''>('');
  const [isScanning, setIsScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);

  // Upload/Fetch Spec Form
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [specName, setSpecName] = useState('');
  const [specVersion, setSpecVersion] = useState('');
  const [specContent, setSpecContent] = useState('');
  const [specUrl, setSpecUrl] = useState('');
  const [activeUploadTab, setActiveUploadTab] = useState<'paste' | 'url'>('paste');
  const [isSubmittingSpec, setIsSubmittingSpec] = useState(false);

  const handleRunScan = async () => {
    if (!prevSpecId || !currSpecId) {
      setScanError('Please select both a previous and a current OpenAPI specification.');
      return;
    }
    setScanError(null);
    setIsScanning(true);
    try {
      const res = await api.triggerScan({
        previous_spec_id: Number(prevSpecId),
        current_spec_id: Number(currSpecId),
        repository_id: repoId ? Number(repoId) : undefined,
      });
      onScanCreated(res);
      onInspectScan(res.id);
    } catch (err: any) {
      setScanError(err.message || 'Scan failed.');
    } finally {
      setIsScanning(false);
    }
  };

  const handleSaveSpec = async () => {
    setIsSubmittingSpec(true);
    try {
      if (activeUploadTab === 'paste') {
        await api.createSpecification({
          name: specName || 'Custom API',
          version: specVersion || '1.0.0',
          content: specContent,
          format: specContent.trim().startsWith('{') ? 'json' : 'yaml',
          source_type: 'upload',
        });
      } else {
        await api.fetchSpecFromUrl(specUrl, specName || undefined);
      }
      setShowUploadModal(false);
      setSpecName('');
      setSpecVersion('');
      setSpecContent('');
      setSpecUrl('');
      onRefresh();
    } catch (err: any) {
      alert(`Failed to save specification: ${err.message}`);
    } finally {
      setIsSubmittingSpec(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-responsive-title font-bold text-[#282719] tracking-tight flex items-center space-x-2.5">
            <FileCode2 className="h-5 w-5 text-[#6D28D9]" />
            <span>OpenAPI Specifications &amp; Diff Engine</span>
          </h1>
          <p className="text-responsive-body text-[#625F4B] mt-1">
            Compare OpenAPI 3.0 / 3.1 contracts with deterministic breaking-change classification
          </p>
        </div>

        <button
          onClick={() => setShowUploadModal(true)}
          className="flex items-center space-x-1.5 rounded-lg bg-[#6D28D9] hover:bg-[#5B21B6] px-3.5 py-2 text-xs font-semibold text-white shadow-xs transition-all self-start sm:self-auto"
        >
          <Plus className="h-3.5 w-3.5" />
          <span>Add OpenAPI Spec</span>
        </button>
      </div>

      {/* Comparison Launcher Box */}
      <div className="apv-panel p-5 space-y-4">
        <h2 className="text-responsive-card font-bold text-[#282719] flex items-center space-x-2">
          <Play className="h-3.5 w-3.5 text-[#6D28D9] fill-current" />
          <span>Launch Contract Diff Comparison</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-bold text-[#625F4B] mb-1.5">Base Specification (Previous)</label>
            <select
              value={prevSpecId}
              onChange={e => setPrevSpecId(e.target.value ? Number(e.target.value) : '')}
              className="w-full rounded-lg bg-white border border-[#DCD3A5] px-3 py-2 text-xs text-[#282719] focus:outline-none focus:border-[#6D28D9] focus:ring-1 focus:ring-[#6D28D9]"
            >
              <option value="">-- Select Base Spec --</option>
              {specifications.map(s => (
                <option key={s.id} value={s.id}>
                  {s.name} (v{s.version})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-[#625F4B] mb-1.5">Target Specification (Current)</label>
            <select
              value={currSpecId}
              onChange={e => setCurrSpecId(e.target.value ? Number(e.target.value) : '')}
              className="w-full rounded-lg bg-white border border-[#DCD3A5] px-3 py-2 text-xs text-[#282719] focus:outline-none focus:border-[#6D28D9] focus:ring-1 focus:ring-[#6D28D9]"
            >
              <option value="">-- Select Target Spec --</option>
              {specifications.map(s => (
                <option key={s.id} value={s.id}>
                  {s.name} (v{s.version})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-[#625F4B] mb-1.5">Target Client Repository</label>
            <select
              value={repoId}
              onChange={e => setRepoId(e.target.value ? Number(e.target.value) : '')}
              className="w-full rounded-lg bg-white border border-[#DCD3A5] px-3 py-2 text-xs text-[#282719] focus:outline-none focus:border-[#6D28D9] focus:ring-1 focus:ring-[#6D28D9]"
            >
              <option value="">-- Optional: Link Repo --</option>
              {repositories.map(r => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {scanError && (
          <div className="rounded-lg bg-[#FEE2E2] border border-[#FECACA] p-3 text-xs font-semibold text-[#DC2626]">
            {scanError}
          </div>
        )}

        <div className="pt-2 flex justify-end">
          <button
            onClick={handleRunScan}
            disabled={isScanning}
            className="flex items-center space-x-1.5 rounded-lg bg-[#6D28D9] hover:bg-[#5B21B6] px-4 py-2 text-xs font-semibold text-white shadow-xs transition-all disabled:opacity-50"
          >
            <Play className={`h-3 w-3 ${isScanning ? 'animate-spin' : 'fill-current'}`} />
            <span>{isScanning ? 'Comparing Specifications...' : 'Run Specification Diff'}</span>
          </button>
        </div>
      </div>

      {/* Scans History Table */}
      <div className="apv-panel p-5 space-y-4">
        <h2 className="text-responsive-card font-bold text-[#282719]">
          Evaluation &amp; Scan History
        </h2>

        {scans.length === 0 ? (
          <div className="text-center py-8 text-xs text-[#77735D]">
            No scans performed yet. Select specifications and click &quot;Run Specification Diff&quot;.
          </div>
        ) : (
          <div className="space-y-3">
            {scans.map(scan => (
              <div
                key={scan.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between rounded-xl bg-white border border-[#DCD3A5] p-4 hover:border-[#C4B982] hover:bg-[#FFFCD3]/20 transition-all shadow-2xs gap-3"
              >
                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs font-bold text-[#6D28D9]">Scan #{scan.id}</span>
                    <span className="rounded bg-[#FFFCD3] px-2 py-0.5 text-[11px] text-[#282719] font-mono border border-[#DCD3A5]">
                      Spec #{scan.previous_spec_id} → #{scan.current_spec_id}
                    </span>
                    <span className="rounded bg-[#DCFCE7] px-2 py-0.5 text-[10px] font-bold text-[#15803D] border border-[#BBF7D0]">
                      {scan.status}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-xs text-[#625F4B]">
                    <span className="flex items-center space-x-1 text-[#DC2626] font-bold">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      <span>{scan.breaking_changes} Breaking</span>
                    </span>
                    <span className="text-[#B45309] font-medium">{scan.warnings} Warnings</span>
                    <span className="text-[#77735D] flex items-center space-x-1">
                      <Clock className="h-3.5 w-3.5" />
                      <span>{new Date(scan.created_at).toLocaleTimeString()}</span>
                    </span>
                  </div>
                </div>

                <button
                  onClick={() => onInspectScan(scan.id)}
                  className="flex items-center space-x-1.5 rounded-lg bg-white hover:bg-[#E6D9A0] px-3.5 py-1.5 text-xs font-semibold text-[#282719] border border-[#DCD3A5] shadow-2xs transition-colors self-start sm:self-auto"
                >
                  <span>Inspect Changes</span>
                  <ArrowRight className="h-3.5 w-3.5 text-[#77735D]" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal for adding spec */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#282719]/40 backdrop-blur-xs p-4">
          <div className="apv-panel w-full max-w-lg p-6 border border-[#DCD3A5] bg-white space-y-4 shadow-2xl rounded-xl">
            <div className="flex items-center justify-between border-b border-[#DCD3A5] pb-3">
              <h3 className="text-responsive-card font-bold text-[#282719]">Add OpenAPI Specification</h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-[#77735D] hover:text-[#282719] p-1 rounded-md hover:bg-[#E6D9A0] transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex border-b border-[#DCD3A5]">
              <button
                onClick={() => setActiveUploadTab('paste')}
                className={`py-2 px-4 text-xs font-bold border-b-2 transition-colors ${
                  activeUploadTab === 'paste'
                    ? 'border-[#6D28D9] text-[#6D28D9]'
                    : 'border-transparent text-[#625F4B] hover:text-[#282719]'
                }`}
              >
                Paste JSON / YAML
              </button>
              <button
                onClick={() => setActiveUploadTab('url')}
                className={`py-2 px-4 text-xs font-bold border-b-2 transition-colors ${
                  activeUploadTab === 'url'
                    ? 'border-[#6D28D9] text-[#6D28D9]'
                    : 'border-transparent text-[#625F4B] hover:text-[#282719]'
                }`}
              >
                Fetch from URL
              </button>
            </div>

            <div className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-[#625F4B] mb-1">API Name</label>
                <input
                  type="text"
                  placeholder="e.g. Store Checkout API"
                  value={specName}
                  onChange={e => setSpecName(e.target.value)}
                  className="w-full rounded-lg bg-white border border-[#DCD3A5] px-3 py-2 text-xs text-[#282719] focus:outline-none focus:border-[#6D28D9] focus:ring-1 focus:ring-[#6D28D9]"
                />
              </div>

              {activeUploadTab === 'paste' ? (
                <>
                  <div>
                    <label className="block text-xs font-bold text-[#625F4B] mb-1">Version</label>
                    <input
                      type="text"
                      placeholder="e.g. 2.0.0"
                      value={specVersion}
                      onChange={e => setSpecVersion(e.target.value)}
                      className="w-full rounded-lg bg-white border border-[#DCD3A5] px-3 py-2 text-xs text-[#282719] focus:outline-none focus:border-[#6D28D9] focus:ring-1 focus:ring-[#6D28D9]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-[#625F4B] mb-1">OpenAPI Content</label>
                    <textarea
                      rows={6}
                      placeholder="Paste OpenAPI 3.0/3.1 JSON or YAML here..."
                      value={specContent}
                      onChange={e => setSpecContent(e.target.value)}
                      className="w-full rounded-lg bg-[#FFFBEA] border border-[#DCD3A5] p-3 text-xs font-mono text-[#282719] leading-relaxed focus:outline-none focus:border-[#6D28D9]"
                    />
                  </div>
                </>
              ) : (
                <div>
                  <label className="block text-xs font-bold text-[#625F4B] mb-1">Remote OpenAPI Spec URL</label>
                  <input
                    type="url"
                    placeholder="https://api.example.com/openapi.json"
                    value={specUrl}
                    onChange={e => setSpecUrl(e.target.value)}
                    className="w-full rounded-lg bg-white border border-[#DCD3A5] px-3 py-2 text-xs text-[#282719] focus:outline-none focus:border-[#6D28D9] focus:ring-1 focus:ring-[#6D28D9]"
                  />
                </div>
              )}
            </div>

            <div className="flex justify-end space-x-2.5 pt-3 border-t border-[#DCD3A5]">
              <button
                onClick={() => setShowUploadModal(false)}
                className="px-3.5 py-2 text-xs font-medium rounded-lg text-[#625F4B] hover:text-[#282719] hover:bg-[#E6D9A0] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveSpec}
                disabled={isSubmittingSpec}
                className="px-4 py-2 text-xs font-bold rounded-lg bg-[#6D28D9] hover:bg-[#5B21B6] text-white shadow-xs disabled:opacity-50 transition-colors"
              >
                {isSubmittingSpec ? 'Saving...' : 'Save Specification'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
