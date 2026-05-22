import { useState } from 'react';
import {
  GitBranch, Search, Star, FileCode, Box, Zap,
  CheckCircle, XCircle, AlertCircle, ChevronRight,
  Lock, Globe, FlaskConical, Package, Layers, Server
} from 'lucide-react';
import { scanRepo, type RepoScanResult } from '../utils/api';
import './RepoScanner.css';

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

  const handleScan = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await scanRepo(url.trim(), token.trim() || undefined);
      setResult(data);
      onRepoScanned(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
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
      </div>

      {/* Input Card */}
      <div className="scan-card">
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

          {/* CI/CD Status */}
          <div className="ci-status-row">
            <div className="ci-status-item">
              <StatusIcon ok={result.metadata.has_ci} />
              <span>{result.metadata.has_ci ? 'CI/CD configured' : 'No CI/CD found'}</span>
            </div>
            <div className="ci-status-item">
              <StatusIcon ok={result.metadata.has_dockerfile} />
              <span>{result.metadata.has_dockerfile ? 'Dockerfile present' : 'No Dockerfile'}</span>
            </div>
            <div className="ci-status-item">
              <StatusIcon ok={result.metadata.has_tests} />
              <span>{result.metadata.has_tests ? 'Tests present' : 'No tests'}</span>
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
