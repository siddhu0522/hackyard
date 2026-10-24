import React, { useState } from 'react';
import {
  FolderGit2,
  GitBranch,
  RefreshCw,
  FileCode,
  Folder,
  Layers,
  ShieldCheck
} from 'lucide-react';
import { Repository } from '../types';
import { api } from '../services/api';

interface RepositoriesViewProps {
  repositories: Repository[];
  onRefresh: () => void;
}

export const RepositoriesView: React.FC<RepositoriesViewProps> = ({ repositories, onRefresh }) => {
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
  const [tree, setTree] = useState<any[]>([]);
  const [loadingTree, setLoadingTree] = useState(false);
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [loadingFile, setLoadingFile] = useState(false);
  const [isDiscovering, setIsDiscovering] = useState(false);

  const handleSelectRepo = async (repo: Repository) => {
    setSelectedRepo(repo);
    setActiveFile(null);
    setFileContent(null);
    setLoadingTree(true);
    try {
      const res = await api.getRepoTree(repo.id);
      setTree(res.tree);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingTree(false);
    }
  };

  const handleViewFile = async (filePath: string) => {
    if (!selectedRepo) return;
    setActiveFile(filePath);
    setLoadingFile(true);
    try {
      const res = await api.getFileContent(selectedRepo.id, filePath);
      setFileContent(res.content);
    } catch (err) {
      console.error(err);
      setFileContent('Failed to load file content.');
    } finally {
      setLoadingFile(false);
    }
  };

  const handleDiscover = async () => {
    setIsDiscovering(true);
    try {
      await api.discoverDemoRepos();
      onRefresh();
    } catch (err) {
      console.error(err);
    } finally {
      setIsDiscovering(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-responsive-title font-bold text-[#282719] tracking-tight flex items-center space-x-2.5">
            <FolderGit2 className="h-5 w-5 text-[#6D28D9]" />
            <span>Target Client Repositories</span>
          </h1>
          <p className="text-responsive-body text-[#625F4B] mt-1">
            Indexed client repositories analyzed for API change impacts, patches, and automated tests
          </p>
        </div>

        <button
          onClick={handleDiscover}
          disabled={isDiscovering}
          className="flex items-center space-x-1.5 rounded-lg bg-white hover:bg-[#E6D9A0] px-3.5 py-2 text-xs font-semibold text-[#282719] border border-[#DCD3A5] shadow-2xs transition-colors self-start sm:self-auto"
        >
          <RefreshCw className={`h-3.5 w-3.5 text-[#6D28D9] ${isDiscovering ? 'animate-spin' : ''}`} />
          <span>Sync Repositories</span>
        </button>
      </div>

      {/* Security Boundary Notice */}
      <div className="rounded-xl bg-[#FFFCD3] p-4 border border-[#DCD3A5] flex items-center justify-between shadow-2xs">
        <div className="flex items-center space-x-3 text-xs">
          <ShieldCheck className="h-4 w-4 text-[#15803D] shrink-0" />
          <span className="text-[#625F4B]">
            <strong className="text-[#282719] font-bold">Repository Boundary Guard: </strong>
            All patches and file edits are strictly restricted to authorized repository roots.
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Repo List (4 cols) */}
        <div className="lg:col-span-4 space-y-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-[#77735D] px-1">
            Registered Repositories ({repositories.length})
          </h2>

          {repositories.length === 0 ? (
            <div className="apv-panel p-6 text-center text-xs text-[#77735D]">
              No repositories found. Click &quot;Sync Repositories&quot; above.
            </div>
          ) : (
            repositories.map(repo => {
              const isSelected = selectedRepo?.id === repo.id;
              return (
                <div
                  key={repo.id}
                  onClick={() => handleSelectRepo(repo)}
                  className={`apv-panel p-4 cursor-pointer transition-all border ${
                    isSelected
                      ? 'border-[#6D28D9] bg-[#FFFCD3] border-l-4 shadow-xs'
                      : 'border-[#DCD3A5] hover:border-[#C4B982] hover:bg-[#FFFCD3]/30'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-[#282719]">{repo.name}</span>
                    <span className="rounded bg-white px-2 py-0.5 text-[10px] font-mono font-semibold text-[#625F4B] border border-[#DCD3A5]">
                      {repo.is_demo ? 'LOCAL DEMO' : 'GITHUB'}
                    </span>
                  </div>

                  <p className="text-xs text-[#77735D] font-mono mt-1.5 truncate">{repo.full_name}</p>

                  <div className="mt-3 flex items-center space-x-3 text-xs text-[#625F4B] font-mono">
                    <span className="flex items-center space-x-1">
                      <GitBranch className="h-3.5 w-3.5 text-[#77735D]" />
                      <span>{repo.default_branch}</span>
                    </span>
                    <span>•</span>
                    <span className="text-[#15803D] font-bold">Indexed</span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Tree & File Inspector (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          {selectedRepo ? (
            <div className="apv-panel p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#DCD3A5] pb-3">
                <div>
                  <h3 className="text-responsive-card font-bold text-[#282719] flex items-center space-x-2">
                    <Layers className="h-4 w-4 text-[#6D28D9]" />
                    <span>{selectedRepo.name} Source Explorer</span>
                  </h3>
                  <span className="text-xs text-[#77735D] font-mono">Branch: {selectedRepo.default_branch}</span>
                </div>
              </div>

              {loadingTree ? (
                <div className="py-8 text-center text-xs text-[#77735D]">Indexing file tree...</div>
              ) : (
                <div className="space-y-2">
                  <span className="text-xs font-bold text-[#77735D] uppercase tracking-wider">
                    Source Files:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {tree.map(item => (
                      <button
                        key={item.path}
                        onClick={() => item.type === 'file' && handleViewFile(item.path)}
                        className={`flex items-center space-x-1.5 rounded-lg px-2.5 py-1.5 text-xs font-mono transition-all ${
                          activeFile === item.path
                            ? 'bg-[#6D28D9] text-white font-semibold shadow-xs'
                            : 'bg-white text-[#282719] hover:bg-[#E6D9A0] border border-[#DCD3A5]'
                        }`}
                      >
                        {item.type === 'dir' ? (
                          <Folder className="h-3.5 w-3.5 text-[#B45309]" />
                        ) : (
                          <FileCode className="h-3.5 w-3.5 text-[#625F4B]" />
                        )}
                        <span>{item.path}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {activeFile && (
                <div className="mt-4 rounded-xl bg-white border border-[#DCD3A5] overflow-hidden shadow-2xs">
                  <div className="flex items-center justify-between bg-[#FFFCD3] px-4 py-2 border-b border-[#DCD3A5]">
                    <span className="font-mono text-xs text-[#282719] font-bold">{activeFile}</span>
                    <span className="text-[10px] text-[#77735D] font-mono bg-white px-1.5 py-0.5 rounded border border-[#DCD3A5]">Read-Only</span>
                  </div>
                  {loadingFile ? (
                    <div className="p-8 text-center text-xs text-[#77735D]">Loading file content...</div>
                  ) : (
                    <pre className="p-4 text-xs font-mono text-[#282719] bg-[#FFFBEA] overflow-x-auto leading-relaxed max-h-96">
                      {fileContent}
                    </pre>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="apv-panel p-12 text-center text-xs text-[#77735D]">
              Select a repository from the left to inspect its file hierarchy and source code.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
