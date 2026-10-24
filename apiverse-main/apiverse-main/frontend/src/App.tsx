import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar, TabKey } from './components/Sidebar';
import { DashboardView } from './views/DashboardView';
import { RepositoriesView } from './views/RepositoriesView';
import { SpecsAndScansView } from './views/SpecsAndScansView';
import { ChangeDetailView } from './views/ChangeDetailView';
import { CodeImpactView } from './views/CodeImpactView';
import { RepairStudioView } from './views/RepairStudioView';
import { VerificationView } from './views/VerificationView';
import { PullRequestsView } from './views/PullRequestsView';
import { MonitoringView } from './views/MonitoringView';
import { SettingsView } from './views/SettingsView';

import {
  DashboardMetrics,
  Repository,
  ApiSpecification,
  ScanDetail,
  DetectedChange,
  AffectedFile,
  RepairAttempt,
  PullRequestRecord,
  NotificationRecord,
  SystemHealth
} from './types';
import { api } from './services/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabKey>('dashboard');
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [specifications, setSpecifications] = useState<ApiSpecification[]>([]);
  const [scans, setScans] = useState<ScanDetail[]>([]);
  const [notifications, setNotifications] = useState<NotificationRecord[]>([]);
  const [pullRequests, setPullRequests] = useState<PullRequestRecord[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);

  // Responsive Mobile Menu State
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Workflow State Across Views
  const [selectedScanId, setSelectedScanId] = useState<number | null>(null);
  const [selectedChange, setSelectedChange] = useState<DetectedChange | null>(null);
  const [affectedFiles, setAffectedFiles] = useState<AffectedFile[]>([]);
  const [selectedRepair, setSelectedRepair] = useState<RepairAttempt | null>(null);

  const [isSeeding, setIsSeeding] = useState(false);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    try {
      const [m, repos, specs, scanList, notifs, prs, health] = await Promise.all([
        api.getMetrics().catch(() => null),
        api.listRepositories().catch(() => []),
        api.listSpecifications().catch(() => []),
        api.listScans().catch(() => []),
        api.listNotifications().catch(() => []),
        api.listPullRequests().catch(() => []),
        api.getHealth().catch(() => null),
      ]);

      if (m) setMetrics(m);
      setRepositories(repos);
      setSpecifications(specs);
      setScans(scanList);
      setNotifications(notifs);
      setPullRequests(prs);
      setSystemHealth(health);

      if (scanList.length > 0 && !selectedScanId) {
        setSelectedScanId(scanList[0].id);
        if (scanList[0].detected_changes && scanList[0].detected_changes.length > 0) {
          setSelectedChange(scanList[0].detected_changes[0]);
        }
      }
    } catch (err) {
      console.error('Error loading initial data:', err);
    }
  };

  const handleSeedDemo = async () => {
    setIsSeeding(true);
    try {
      await api.seedDemoData();
      await loadAllData();
      setActiveTab('dashboard');
    } catch (err: any) {
      alert(`Demo seeding error: ${err.message}`);
    } finally {
      setIsSeeding(false);
    }
  };

  const handleInspectScan = async (scanId: number) => {
    setSelectedScanId(scanId);
    try {
      const scanDetail = await api.getScan(scanId);
      if (scanDetail.detected_changes && scanDetail.detected_changes.length > 0) {
        setSelectedChange(scanDetail.detected_changes[0]);
      }
    } catch (err) {
      console.error(err);
    }
    setActiveTab('changes');
  };

  const handleAnalyzeImpact = async (change: DetectedChange) => {
    setSelectedChange(change);
    // Find target repo
    const targetRepo = repositories[0];
    if (targetRepo) {
      try {
        const files = await api.analyzeCodeImpact(change.id, targetRepo.id);
        setAffectedFiles(files);
      } catch (err) {
        console.error('Impact analysis error:', err);
      }
    }
    setActiveTab('impact');
  };

  const handleGoToRepair = (change: DetectedChange) => {
    setSelectedChange(change);
    setActiveTab('repairs');
  };

  const handleGoToVerification = (repair: RepairAttempt) => {
    setSelectedRepair(repair);
    setActiveTab('verifications');
  };

  const handleGoToPR = async (repair: RepairAttempt) => {
    setSelectedRepair(repair);
    try {
      await api.createPullRequest(repair.id);
      const prs = await api.listPullRequests();
      setPullRequests(prs);
    } catch (err: any) {
      alert(`PR creation notice: ${err.message}`);
    }
    setActiveTab('pull_requests');
  };

  const handleGlobalSearch = (query: string) => {
    const q = query.toLowerCase();
    if (q.includes('repo') || q.includes('git')) {
      setActiveTab('repositories');
    } else if (q.includes('spec') || q.includes('scan') || q.includes('diff')) {
      setActiveTab('specs');
    } else if (q.includes('change') || q.includes('break') || q.includes('endpoint')) {
      setActiveTab('changes');
    } else if (q.includes('impact') || q.includes('ast')) {
      setActiveTab('impact');
    } else if (q.includes('repair') || q.includes('ai') || q.includes('patch')) {
      setActiveTab('repairs');
    } else if (q.includes('verify') || q.includes('test')) {
      setActiveTab('verifications');
    } else if (q.includes('pr') || q.includes('pull')) {
      setActiveTab('pull_requests');
    } else if (q.includes('monitor') || q.includes('schedule') || q.includes('hook')) {
      setActiveTab('monitoring');
    } else if (q.includes('setting') || q.includes('health') || q.includes('config')) {
      setActiveTab('settings');
    } else {
      setActiveTab('changes');
    }
  };

  return (
    <div className="min-h-screen bg-[#FFFBEA] text-[#282719] flex flex-col antialiased">
      <Navbar
        notifications={notifications}
        onRefreshNotifications={loadAllData}
        onSeedDemo={handleSeedDemo}
        isSeeding={isSeeding}
        systemHealth={systemHealth}
        onSearchSelect={handleGlobalSearch}
        onToggleMobileMenu={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        isMobileMenuOpen={isMobileMenuOpen}
      />

      <div className="flex flex-1 relative">
        <Sidebar
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          breakingCount={metrics?.counts.breaking_changes || 0}
          openPrCount={pullRequests.length}
          systemHealth={systemHealth}
          mobileOpen={isMobileMenuOpen}
          onCloseMobile={() => setIsMobileMenuOpen(false)}
        />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto max-w-7xl w-full mx-auto">
          {activeTab === 'dashboard' && (
            <DashboardView
              metrics={metrics}
              scans={scans}
              pullRequests={pullRequests}
              notifications={notifications}
              onNavigate={setActiveTab}
              onInspectScan={handleInspectScan}
            />
          )}

          {activeTab === 'repositories' && (
            <RepositoriesView repositories={repositories} onRefresh={loadAllData} />
          )}

          {activeTab === 'specs' && (
            <SpecsAndScansView
              specifications={specifications}
              repositories={repositories}
              scans={scans}
              onScanCreated={(newScan) => {
                setScans([newScan, ...scans]);
                setSelectedScanId(newScan.id);
                loadAllData();
              }}
              onRefresh={loadAllData}
              onInspectScan={handleInspectScan}
            />
          )}

          {activeTab === 'changes' && (
            <ChangeDetailView
              scans={scans}
              selectedScanId={selectedScanId}
              onSelectScan={handleInspectScan}
              onAnalyzeImpact={handleAnalyzeImpact}
              onGoToRepair={handleGoToRepair}
            />
          )}

          {activeTab === 'impact' && (
            <CodeImpactView
              selectedChange={selectedChange}
              affectedFiles={affectedFiles}
              onTriggerRepair={handleGoToRepair}
            />
          )}

          {activeTab === 'repairs' && (
            <RepairStudioView
              selectedChange={selectedChange}
              onGoToVerification={handleGoToVerification}
            />
          )}

          {activeTab === 'verifications' && (
            <VerificationView
              selectedRepair={selectedRepair}
              onGoToPR={handleGoToPR}
            />
          )}

          {activeTab === 'pull_requests' && (
            <PullRequestsView
              pullRequests={pullRequests}
              onRefresh={loadAllData}
            />
          )}

          {activeTab === 'monitoring' && (
            <MonitoringView
              repositories={repositories}
              notifications={notifications}
              onRefreshNotifications={loadAllData}
            />
          )}

          {activeTab === 'settings' && (
            <SettingsView
              onSeedDemo={handleSeedDemo}
              isSeeding={isSeeding}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
