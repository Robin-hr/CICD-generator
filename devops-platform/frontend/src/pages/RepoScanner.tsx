import { useState } from 'react';
import {
  GitBranch, Search, Star, FileCode, Box, Zap,
  CheckCircle, XCircle, AlertCircle, ChevronRight,
  Lock, Globe, FlaskConical, Package, Layers, Server
} from 'lucide-react';
import { scanRepo, type RepoScanResult, type RepoNode } from '../utils/api';
import RepoStructureTree from './RepoStructureTree';
import './RepoScanner.css';
import './RepoStructureTree.css';

interface Props {
  onRepoScanned: (result: RepoScanResult) => void;
  onGoToCICD: () => void;
  scannedRepo: RepoScanResult | null;
}

const LANG_COLORS: Record<string, string> = {
  Python: '#3776ab', JavaScript: '#f7df1e', TypeScript: '#3178c6',
  Java: '#ed8b00', Go: '#00add8', Rust: '#dea584', Ruby: '#cc342d',
  'C#': '#9b4f97', 'C++': '#f34b7d', PHP: '#4f5d95', Kotlin: '#7f52ff',
};

const EXAMPLE_REPOS = [
  'https://github.com/tiangolo/fastapi',
  'https://github.com/facebook/react',
  'https://github.com/gin-gonic/gin',
  'https://github.com/spring-projects/spring-boot',
];

export default function RepoScanner({ onRepoScanned, onGoToCICD, scannedRepo }: Props) {
  const [url, setUrl] = useState('');
  const [token, setToken] = useState('');
  const [showToken, setShowToken] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<RepoScanResult | null>(scannedRepo);
  const [useAIAnalysis, setUseAIAnalysis] = useState(true);
  const [manualMode, setManualMode] = useState(false);
  const [manualInput, setManualInput] = useState('');

  const handleScan = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setError('');
    try {
      const aiConfig = useAIAnalysis ? {
        api_key: 'placeholder', // Frontend should ideally have a place to enter this
        model: 'gpt-3.5-turbo'
      } : undefined;
      
      const data = await scanRepo(url.trim(), token.trim() || undefined);
      setResult(data);
      onRepoScanned(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleManualSubmit = () => {
    // Basic heuristics to construct a RepoScanResult from manual input
    const mockResult: RepoScanResult = {
      owner: 'manual',
      repo: 'project',
      repo_url: '',
      description: 'Manually provided structure',
      default_branch: 'main',
      stars: 0,
      language: { primary: 'Mixed', all: {} },
      framework: 'Detected from structure',
      package_manager: 'Detected',
      deployment_styles: [],
      test_framework: 'Unknown',
      metadata: {
        total_files: 0,
        has_dockerfile: manualInput.includes('Dockerfile'),
        has_ci: false,
        has_tests: manualInput.includes('test'),
        private: true,
        topics: []
      },
      file_tree_sample: manualInput.split('\n').map(l => l.trim()),
      file_tree_hierarchical: [], // We'd need a parser here
      structure_descriptions: {}
    };
    setResult(mockResult);
    onRepoScanned(mockResult);
  };

  const StatusIcon = ({ ok }: { ok: boolean }) =>
    ok ? <CheckCircle size={14} className="status-ok" /> : <XCircle size={14} className="status-no" />;

  const langPercent = result?.language.all ?? {};
  const topLangs = Object.entries(langPercent)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  return (
    <div className="scanner-page animate-slide-up">
      {/* Header */}
      <div className="page-header">
        <div className="page-header__icon">
          <GitBranch size={20} />
        </div>
        <div>
          <h1 className="page-title">Repository Scanner</h1>
          <p className="page-subtitle">Detect language, framework, package manager & deployment style</p>
        </div>
        <div className="mode-toggle">
          <button 
            className={`mode-btn ${!manualMode ? 'active' : ''}`} 
            onClick={() => setManualMode(false)}
          >
            Auto Scan
          </button>
          <button 
            className={`mode-btn ${manualMode ? 'active' : ''}`} 
            onClick={() => setManualMode(true)}
          >
            Manual Structure
          </button>
        </div>
      </div>

      {/* Input Card */}
      <div className="scan-card">
        {!manualMode ? (
          <>
            <div className="scan-card__input-row">
              <div className="input-wrapper">
                <GitBranch size={14} className="input-icon" />
                <input
                  className="repo-input"
                  type="text"
                  placeholder="https://github.com/owner/repository"
                  value={url}
                  onChange={e => setUrl(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleScan()}
                  spellCheck={false}
                />
              </div>
              <button
                className={`scan-btn ${loading ? 'scan-btn--loading' : ''}`}
                onClick={handleScan}
                disabled={loading || !url.trim()}
              >
                {loading ? (
                  <>
                    <span className="spinner" />
                    Scanning...
                  </>
                ) : (
                  <>
                    <Search size={14} />
                    Scan Repo
                  </>
                )}
              </button>
            </div>

            {/* Token toggle */}
            <div className="token-row">
              <button className="token-toggle" onClick={() => setShowToken(!showToken)}>
                <Lock size={11} />
                {showToken ? 'Hide' : 'Add'} GitHub Token (optional, avoids rate limits)
              </button>
            </div>
            {showToken && (
              <div className="token-input-row">
                <input
                  className="token-input"
                  type="password"
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                  value={token}
                  onChange={e => setToken(e.target.value)}
                />
              </div>
            )}

            {/* AI Toggle */}
            <div className="ai-toggle-row">
               <label className="checkbox-label">
                  <input type="checkbox" checked={useAIAnalysis} onChange={e => setUseAIAnalysis(e.target.checked)} />
                  <span>Use AI Structure Analysis (Premium)</span>
                  <Zap size={10} className="zap-icon" />
               </label>
            </div>

            {/* Examples */}
            <div className="examples-row">
              <span className="examples-label">Try:</span>
              {EXAMPLE_REPOS.map(repo => {
                const short = repo.replace('https://github.com/', '');
                return (
                  <button key={repo} className="example-chip" onClick={() => setUrl(repo)}>
                    {short}
                  </button>
                );
              })}
            </div>
          </>
        ) : (
          <div className="manual-input-section">
            <p className="manual-hint">Paste your repository folder structure or describe your project setup below.</p>
            <textarea
              className="manual-textarea"
              placeholder="Example:&#10;backend/&#10;  main.py (FastAPI)&#10;  requirements.txt&#10;frontend/&#10;  src/App.tsx (React)&#10;  package.json"
              value={manualInput}
              onChange={e => setManualInput(e.target.value)}
            />
            <button className="cta-btn cta-btn--manual" onClick={handleManualSubmit} disabled={!manualInput.trim()}>
              Process Structure
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="error-banner animate-fade-in">
          <AlertCircle size={15} />
          <span>{error}</span>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="results animate-slide-up">
          {/* Repo Header */}
          <div className="result-repo-header">
            <div className="result-repo-info">
              {result.metadata.private ? <Lock size={16} /> : <Globe size={16} />}
              <div>
                <h2 className="result-repo-name">{result.owner}/{result.repo}</h2>
                {result.description && (
                  <p className="result-repo-desc">{result.description}</p>
                )}
              </div>
            </div>
            <div className="result-repo-meta">
              <div className="meta-chip">
                <Star size={12} />
                {result.stars.toLocaleString()}
              </div>
              <div className="meta-chip">
                <FileCode size={12} />
                {result.metadata.total_files} files
              </div>
              <div className="meta-chip">
                <GitBranch size={12} />
                {result.default_branch}
              </div>
            </div>
          </div>

          {/* Detection Grid */}
          <div className="detection-grid">
            {/* Language */}
            <div className="detect-card">
              <div className="detect-card__header">
                <FileCode size={14} />
                Language
              </div>
              <div className="detect-card__primary" style={{ color: LANG_COLORS[result.language.primary] || 'var(--accent-cyan)' }}>
                {result.language.primary}
              </div>
              <div className="lang-bars">
                {topLangs.map(([lang, pct]) => (
                  <div key={lang} className="lang-bar-row">
                    <div
                      className="lang-dot"
                      style={{ background: LANG_COLORS[lang] || 'var(--text-muted)' }}
                    />
                    <span className="lang-name">{lang}</span>
                    <div className="lang-track">
                      <div
                        className="lang-fill"
                        style={{
                          width: `${pct}%`,
                          background: LANG_COLORS[lang] || 'var(--accent-cyan)'
                        }}
                      />
                    </div>
                    <span className="lang-pct">{pct}%</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Framework */}
            <div className="detect-card">
              <div className="detect-card__header">
                <Layers size={14} />
                Framework
              </div>
              <div className="detect-card__primary">{result.framework}</div>
              <div className="detect-card__sub">Auto-detected from dependencies</div>
            </div>

            {/* Package Manager */}
            <div className="detect-card">
              <div className="detect-card__header">
                <Package size={14} />
                Package Manager
              </div>
              <div className="detect-card__primary">{result.package_manager}</div>
              <div className="detect-card__sub">Detected from lock files</div>
            </div>

            {/* Test Framework */}
            <div className="detect-card">
              <div className="detect-card__header">
                <FlaskConical size={14} />
                Test Framework
              </div>
              <div className="detect-card__primary">{result.test_framework}</div>
              <div className="detect-card__sub">
                <StatusIcon ok={result.metadata.has_tests} />
                {result.metadata.has_tests ? ' Tests found' : ' No tests detected'}
              </div>
            </div>
          </div>

          {/* Deployment Styles */}
          <div className="detect-card detect-card--wide">
            <div className="detect-card__header">
              <Server size={14} />
              Deployment Style
            </div>
            <div className="deployment-chips">
              {result.deployment_styles.map(d => (
                <span key={d} className="deployment-chip">
                  {d === 'Docker' && <Box size={12} />}
                  {d === 'GitHub Actions' && <Zap size={12} />}
                  {d}
                </span>
              ))}
            </div>
          </div>

          {/* New Visual Structure Tree */}
          <div className="structure-tree-section">
            <div className="section-header">
              <Layers size={14} />
              Repository Structure
            </div>
            <div className="structure-tree-container">
              {result.file_tree_hierarchical && result.file_tree_hierarchical.length > 0 ? (
                <RepoStructureTree 
                  data={result.file_tree_hierarchical} 
                  descriptions={result.structure_descriptions} 
                />
              ) : (
                <div className="tree-empty">
                  No structure data available for this view.
                </div>
              )}
            </div>
          </div>

          {/* Topics */}
          {result.metadata.topics.length > 0 && (
            <div className="topics-row">
              {result.metadata.topics.map(t => (
                <span key={t} className="topic-tag">#{t}</span>
              ))}
            </div>
          )}

          {/* CTA */}
          <div className="cta-section">
            <div className="cta-text">
              <CheckCircle size={16} className="status-ok" />
              <span>Scan complete! Generate your CI/CD pipeline now.</span>
            </div>
            <button className="cta-btn" onClick={onGoToCICD}>
              Generate CI/CD Pipeline
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!result && !loading && (
        <div className="empty-state">
          <div className="empty-state__icon">
            <GitBranch size={32} />
          </div>
          <h3>Paste a GitHub URL to begin</h3>
          <p>We'll detect your stack and generate ready-to-use DevOps configs.</p>
        </div>
      )}
    </div>
  );
}
