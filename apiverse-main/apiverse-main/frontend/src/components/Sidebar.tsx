import React from 'react';
import {
  LayoutDashboard,
  FolderGit2,
  FileCode2,
  AlertTriangle,
  LocateFixed,
  Wrench,
  Terminal,
  GitPullRequest,
  Activity,
  Settings,
  Database,
  X
} from 'lucide-react';
import { SystemHealth } from '../types';

export type TabKey =
  | 'dashboard'
  | 'repositories'
  | 'specs'
  | 'changes'
  | 'impact'
  | 'repairs'
  | 'verifications'
  | 'pull_requests'
  | 'monitoring'
  | 'settings';

interface SidebarProps {
  activeTab: TabKey;
  onSelectTab: (tab: TabKey) => void;
  breakingCount?: number;
  openPrCount?: number;
  systemHealth: SystemHealth | null;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

interface NavItem {
  id: TabKey;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
  badgeColor?: 'coral' | 'violet' | 'amber' | 'emerald';
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  breakingCount = 0,
  openPrCount = 0,
  systemHealth,
  mobileOpen = false,
  onCloseMobile,
}) => {
  const groups: NavGroup[] = [
    {
      title: 'Workspace',
      items: [
        { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
        { id: 'repositories', label: 'Repositories', icon: FolderGit2 },
        { id: 'specs', label: 'API Specifications', icon: FileCode2 },
        { id: 'changes', label: 'Breaking Changes', icon: AlertTriangle, badge: breakingCount, badgeColor: 'coral' },
        { id: 'impact', label: 'Code Impact', icon: LocateFixed },
      ],
    },
    {
      title: 'Automation',
      items: [
        { id: 'repairs', label: 'AI Repair Studio', icon: Wrench },
        { id: 'verifications', label: 'Test Verification', icon: Terminal },
        { id: 'pull_requests', label: 'Pull Requests', icon: GitPullRequest, badge: openPrCount, badgeColor: 'violet' },
        { id: 'monitoring', label: 'Monitoring', icon: Activity },
      ],
    },
    {
      title: 'System',
      items: [
        { id: 'settings', label: 'Settings & Integrations', icon: Settings },
      ],
    },
  ];

  const isDbConnected = systemHealth?.database === 'connected';

  const handleItemClick = (id: TabKey) => {
    onSelectTab(id);
    if (onCloseMobile) {
      onCloseMobile();
    }
  };

  const sidebarContent = (
    <div className="flex flex-col justify-between h-full py-4 px-3 select-none">
      <div className="space-y-5">
        {onCloseMobile && (
          <div className="flex md:hidden items-center justify-between pb-2 border-b border-[#DCD3A5]">
            <span className="text-xs font-bold text-[#282719] uppercase tracking-wider">Navigation</span>
            <button
              onClick={onCloseMobile}
              className="p-1 rounded-md text-[#625F4B] hover:bg-[#E6D9A0] transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {groups.map((group, groupIdx) => (
          <div key={groupIdx} className="space-y-1">
            <div className="px-3 py-1 text-[11px] font-bold tracking-wider text-[#77735D] uppercase">
              {group.title}
            </div>
            {group.items.map(item => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleItemClick(item.id)}
                  className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-responsive-nav font-medium transition-all ${
                    isActive
                      ? 'bg-[#E6D9A0] text-[#282719] font-bold border-l-3 border-[#6D28D9] shadow-2xs'
                      : 'text-[#625F4B] hover:bg-[#E6D9A0]/70 hover:text-[#282719] border-l-3 border-transparent'
                  }`}
                >
                  <div className="flex items-center space-x-2.5 truncate">
                    <Icon className={`h-4 w-4 shrink-0 ${isActive ? 'text-[#6D28D9]' : 'text-[#77735D]'}`} />
                    <span className="truncate">{item.label}</span>
                  </div>
                  {item.badge !== undefined && item.badge > 0 && (
                    <span
                      className={`ml-1.5 rounded-full px-2 py-0.5 text-[10px] font-mono font-bold leading-none shrink-0 ${
                        item.badgeColor === 'coral'
                          ? 'bg-[#FEE2E2] text-[#DC2626] border border-[#FECACA]'
                          : 'bg-[#EDE9FE] text-[#6D28D9] border border-[#DDD6FE]'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* System Status Footnote at Bottom */}
      <div className="pt-3 border-t border-[#DCD3A5] space-y-2 px-1">
        <div className="rounded-xl bg-white p-3 border border-[#DCD3A5] shadow-2xs text-xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[#625F4B] font-medium flex items-center space-x-1.5">
              <Database className="h-3.5 w-3.5 text-[#77735D]" />
              <span className="font-semibold text-[#282719]">SQLite Engine</span>
            </span>
            <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-bold ${
              isDbConnected ? 'text-[#15803D] bg-[#DCFCE7] border border-[#BBF7D0]' : 'text-[#DC2626] bg-[#FEE2E2] border border-[#FECACA]'
            }`}>
              {isDbConnected ? 'ACTIVE' : 'ERROR'}
            </span>
          </div>
          <div className="text-[11px] text-[#77735D] font-mono truncate">
            {systemHealth?.version ? `v${systemHealth.version}` : 'v1.0.0'} • Local Storage
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex w-60 xl:w-64 border-r border-[#DCD3A5] bg-[#F5EDC2] flex-col sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto shrink-0 transition-colors">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Backdrop */}
      {mobileOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 z-50 bg-[#282719]/40 backdrop-blur-xs md:hidden transition-opacity"
        />
      )}

      {/* Mobile Drawer Content */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 max-w-[80vw] bg-[#F5EDC2] border-r border-[#DCD3A5] shadow-2xl transform transition-transform duration-300 ease-in-out md:hidden ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {sidebarContent}
      </aside>
    </>
  );
};

