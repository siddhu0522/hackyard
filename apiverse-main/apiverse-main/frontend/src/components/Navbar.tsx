import React, { useState } from 'react';
import {
  Search,
  Bell,
  RefreshCw,
  Sparkles,
  Database,
  Menu,
  X,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { APIVerseLogo } from './APIVerseLogo';
import { NotificationRecord, SystemHealth } from '../types';

interface NavbarProps {
  notifications: NotificationRecord[];
  onRefreshNotifications: () => void;
  onSeedDemo: () => void;
  isSeeding: boolean;
  systemHealth: SystemHealth | null;
  onSearchSelect?: (query: string) => void;
  onToggleMobileMenu?: () => void;
  isMobileMenuOpen?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  notifications,
  onRefreshNotifications,
  onSeedDemo,
  isSeeding,
  systemHealth,
  onSearchSelect,
  onToggleMobileMenu,
  isMobileMenuOpen = false
}) => {
  const [showNotifications, setShowNotifications] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const unreadCount = notifications.filter(n => !n.is_read).length;

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSearchSelect && searchQuery.trim()) {
      onSearchSelect(searchQuery.trim());
    }
  };

  const isHealthy = systemHealth?.database === 'connected';

  return (
    <header className="sticky top-0 z-40 w-full border-b border-[#DCD3A5] bg-[#EDE4B0]/95 backdrop-blur-md transition-colors">
      <div className="flex h-14 items-center justify-between px-4 sm:px-6">
        {/* Left: Mobile Toggle, Branding and Workspace Indicator */}
        <div className="flex items-center space-x-3 sm:space-x-5">
          {onToggleMobileMenu && (
            <button
              onClick={onToggleMobileMenu}
              className="md:hidden p-1.5 rounded-lg text-[#282719] hover:bg-[#E6D9A0] transition-colors"
              aria-label="Toggle navigation menu"
            >
              {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          )}

          <div className="flex items-center space-x-2.5">
            <APIVerseLogo size={24} className="h-6 w-6 text-[#6D28D9]" />
            <div className="flex items-baseline space-x-1.5">
              <span className="text-base sm:text-lg font-bold tracking-tight text-[#282719]">APIVerse</span>
              <span className="rounded bg-[#FFFCD3] px-1.5 py-0.5 text-[10px] font-semibold text-[#6D28D9] border border-[#DCD3A5] uppercase tracking-wide">
                Platform
              </span>
            </div>
          </div>

          <div className="hidden md:flex items-center space-x-2 border-l border-[#DCD3A5] pl-4">
            <span className="text-xs text-[#625F4B] font-medium">Workspace:</span>
            <div className="flex items-center space-x-1.5 rounded-md bg-[#FFFCD3] px-2.5 py-1 text-xs text-[#282719] border border-[#DCD3A5] font-mono">
              <span className="h-2 w-2 rounded-full bg-[#6D28D9]"></span>
              <span className="font-medium text-[#282719]">default-workspace</span>
            </div>
          </div>
        </div>

        {/* Center: Global Search Bar */}
        <div className="hidden lg:flex flex-1 max-w-md mx-6">
          <form onSubmit={handleSearchSubmit} className="relative w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#77735D]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search repositories, specs, breaking changes, PRs..."
              className="w-full rounded-lg bg-white border border-[#DCD3A5] pl-9 pr-12 py-1.5 text-xs text-[#282719] placeholder-[#77735D] focus:outline-none focus:border-[#6D28D9] focus:ring-1 focus:ring-[#6D28D9] transition-all font-sans shadow-2xs"
            />
            <kbd className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded bg-[#FFFCD3] px-1.5 py-0.5 text-[10px] font-mono text-[#77735D] border border-[#DCD3A5]">
              ⌘K
            </kbd>
          </form>
        </div>

        {/* Right: Actions, Notifications, Health & Profile */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          {/* Environment Mode Pill */}
          <div className="hidden xl:flex items-center space-x-1.5 rounded-md bg-[#FFFCD3] px-2.5 py-1 text-xs text-[#282719] border border-[#DCD3A5]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#6D28D9]"></span>
            <span className="text-[#625F4B]">Mode:</span>
            <span className="font-semibold text-[#282719]">Demo &amp; GitHub</span>
          </div>

          {/* Seed Demo Action Button */}
          <button
            onClick={onSeedDemo}
            disabled={isSeeding}
            className="flex items-center space-x-1.5 rounded-lg bg-white hover:bg-[#E6D9A0] px-2.5 sm:px-3 py-1.5 text-xs font-semibold text-[#282719] border border-[#DCD3A5] shadow-2xs transition-colors disabled:opacity-50"
            title="Populate complete demonstration scenario with OpenAPI diff, impact analysis, and PR"
          >
            <Sparkles className={`h-3.5 w-3.5 text-[#6D28D9] ${isSeeding ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">{isSeeding ? 'Seeding...' : 'Seed Demo'}</span>
          </button>

          {/* Notifications Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative rounded-lg p-1.5 text-[#625F4B] hover:bg-[#E6D9A0] hover:text-[#282719] transition-colors border border-transparent hover:border-[#DCD3A5]"
              aria-label="Notifications"
            >
              <Bell className="h-4 w-4" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 flex h-2 w-2 rounded-full bg-[#DC2626]"></span>
              )}
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 rounded-xl bg-white border border-[#DCD3A5] p-3.5 shadow-xl z-50">
                <div className="flex items-center justify-between pb-2 border-b border-[#DCD3A5]">
                  <span className="text-xs font-bold text-[#282719]">Notifications</span>
                  <button onClick={onRefreshNotifications} className="text-[#625F4B] hover:text-[#282719] transition-colors">
                    <RefreshCw className="h-3 w-3" />
                  </button>
                </div>
                <div className="mt-2.5 max-h-64 overflow-y-auto space-y-2">
                  {notifications.length === 0 ? (
                    <p className="text-xs text-[#77735D] text-center py-4">No notifications.</p>
                  ) : (
                    notifications.map(n => (
                      <div key={n.id} className="rounded-lg bg-[#FFFBEA] p-2.5 text-xs border border-[#DCD3A5]">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-[#282719]">{n.title}</span>
                          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                            n.severity === 'error'
                              ? 'bg-[#FEE2E2] text-[#DC2626] border border-[#FECACA]'
                              : 'bg-[#EDE9FE] text-[#6D28D9] border border-[#DDD6FE]'
                          }`}>
                            {n.severity}
                          </span>
                        </div>
                        <p className="text-[#625F4B] mt-1 text-[11px] leading-relaxed">{n.message}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Real Health Indicator */}
          <div className="flex items-center space-x-1.5 rounded-md bg-[#FFFCD3] px-2.5 py-1 text-xs border border-[#DCD3A5]">
            <span className={`h-2 w-2 rounded-full ${isHealthy ? 'bg-[#15803D]' : 'bg-[#DC2626]'}`}></span>
            <span className="text-[#625F4B] font-medium hidden sm:inline">DB:</span>
            <span className={`font-semibold ${isHealthy ? 'text-[#15803D]' : 'text-[#DC2626]'}`}>
              {isHealthy ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
