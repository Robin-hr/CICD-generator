import { useState } from 'react';
import { Terminal, GitBranch, Cpu, Shield, Box, Cloud, Menu, X, Zap } from 'lucide-react';
import RepoScanner from './pages/RepoScanner';
import CICDGenerator from './pages/CICDGenerator';
import type { RepoScanResult } from './utils/api';
import './App.css';

type Page = 'scanner' | 'cicd';

const NAV_ITEMS = [
  { id: 'scanner' as Page, label: 'Repo Scanner', icon: GitBranch, badge: 'LIVE' },
  { id: 'cicd' as Page, label: 'CI/CD Generator', icon: Zap, badge: 'LIVE' },
];

const COMING_SOON = [
  { label: 'Docker Generator', icon: Box },
  { label: 'Kubernetes', icon: Cpu },
  { label: 'Terraform', icon: Cloud },
  { label: 'Security Scanner', icon: Shield },
];

export default function App() {
  const [page, setPage] = useState<Page>('scanner');
  const [scannedRepo, setScannedRepo] = useState<RepoScanResult | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  const handleRepoScanned = (result: RepoScanResult) => {
    setScannedRepo(result);
  };

  const handleGoToCICD = () => {
    setPage('cicd');
  };

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className={`sidebar ${menuOpen ? 'sidebar--open' : ''}`}>
        <div className="sidebar__header">
          <div className="sidebar__logo">
            <div className="logo-icon">
              <Terminal size={18} />
            </div>
            <div>
              <div className="logo-title">DevOps</div>
              <div className="logo-sub">Platform v1.0</div>
            </div>
          </div>
          <button className="menu-close" onClick={() => setMenuOpen(false)}>
            <X size={16} />
          </button>
        </div>

        <div className="sidebar__section-label">ACTIVE MODULES</div>
        <nav className="sidebar__nav">
          {NAV_ITEMS.map(({ id, label, icon: Icon, badge }) => (
            <button
              key={id}
              className={`nav-item ${page === id ? 'nav-item--active' : ''}`}
              onClick={() => { setPage(id); setMenuOpen(false); }}
            >
              <Icon size={15} />
              <span>{label}</span>
              {badge && <span className="nav-badge">{badge}</span>}
            </button>
          ))}
        </nav>

        <div className="sidebar__section-label" style={{ marginTop: '24px' }}>COMING SOON</div>
        <nav className="sidebar__nav">
          {COMING_SOON.map(({ label, icon: Icon }) => (
            <div key={label} className="nav-item nav-item--disabled">
              <Icon size={15} />
              <span>{label}</span>
              <span className="nav-badge nav-badge--soon">SOON</span>
            </div>
          ))}
        </nav>

        <div className="sidebar__footer">
          <div className="status-dot" />
          <span>API Connected</span>
        </div>
      </aside>

      {/* Main */}
      <div className="main-area">
        <header className="topbar">
          <button className="menu-btn" onClick={() => setMenuOpen(true)}>
            <Menu size={18} />
          </button>
          <div className="topbar__breadcrumb">
            <span className="topbar__section">DevOps Platform</span>
            <span className="topbar__sep">/</span>
            <span className="topbar__page">
              {NAV_ITEMS.find(n => n.id === page)?.label}
            </span>
          </div>
          {scannedRepo && (
            <div className="topbar__repo-badge">
              <GitBranch size={12} />
              <span>{scannedRepo.owner}/{scannedRepo.repo}</span>
            </div>
          )}
        </header>

        <main className="content">
          {page === 'scanner' && (
            <RepoScanner
              onRepoScanned={handleRepoScanned}
              onGoToCICD={handleGoToCICD}
              scannedRepo={scannedRepo}
            />
          )}
          {page === 'cicd' && (
            <CICDGenerator scannedRepo={scannedRepo} />
          )}
        </main>
      </div>

      {menuOpen && <div className="sidebar__overlay" onClick={() => setMenuOpen(false)} />}
    </div>
  );
}
