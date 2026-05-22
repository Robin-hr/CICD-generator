import { useState } from 'react';
import { Zap, AlertTriangle, Copy, Check, Download, ChevronDown, ChevronUp, Github, Server, Gitlab, MessageSquare, Send, X } from 'lucide-react';
import { generateCICD, chatPipeline, type RepoScanResult, type CICDResult } from '../utils/api';
import './CICDGenerator.css';

interface Props {
  scannedRepo: RepoScanResult | null;
}

type Platform = 'github_actions' | 'jenkins' | 'gitlab_ci';

const PLATFORMS: { id: Platform; name: string; desc: string; icon: React.ReactNode; color: string }[] = [
  {
    id: 'github_actions',
    name: 'GitHub Actions',
    desc: 'Native GitHub CI/CD with YAML workflows',
    icon: <Github size={20} />,
    color: 'var(--accent-cyan)',
  },
  {
    id: 'jenkins',
    name: 'Jenkinsfile',
    desc: 'Jenkins declarative pipeline (Groovy DSL)',
    icon: <Server size={20} />,
    color: 'var(--accent-orange)',
  },
  {
    id: 'gitlab_ci',
    name: 'GitLab CI',
    desc: 'GitLab CI/CD with .gitlab-ci.yml',
    icon: <Gitlab size={20} />,
    color: 'var(--accent-purple)',
  },
];

export default function CICDGenerator({ scannedRepo }: Props) {
  const [selectedPlatform, setSelectedPlatform] = useState<Platform>('github_actions');
  const [result, setResult] = useState<CICDResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [showRaw, setShowRaw] = useState(false);
  const [useAi, setUseAi] = useState(false);
  const [aiConfig, setAiConfig] = useState({
    api_key: '',
    model: 'openai/gpt-oss-120b',
    base_url: 'https://api.groq.com/openai/v1' // Defaulting to Groq based on key prefix
  });
  const [targetCloud, setTargetCloud] = useState('AWS');
  const [deploymentStrategy, setDeploymentStrategy] = useState('EC2/VM');
  const [chatOpen, setChatOpen] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<{role: 'user' | 'assistant', content: string}[]>([]);

  const handleGenerate = async () => {
    if (!scannedRepo) return;
    setLoading(true);
    setError('');
    try {
      const data = await generateCICD(
        scannedRepo, 
        selectedPlatform, 
        useAi, 
        useAi ? aiConfig : undefined,
        targetCloud,
        deploymentStrategy
      );
      setResult(data);
      setShowRaw(false);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!result) return;
    await navigator.clipboard.writeText(result.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!result) return;
    const blob = new Blob([result.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const filename = result.filename.split('/').pop() || 'ci-cd-config';
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || !result || !scannedRepo || chatLoading) return;

    const userMessage = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setChatLoading(true);

    try {
      const response = await chatPipeline(
        result.content,
        userMessage,
        scannedRepo,
        selectedPlatform,
        useAi ? aiConfig : undefined
      );
      setChatMessages(prev => [...prev, { role: 'assistant', content: response }]);
    } catch (e: unknown) {
      setChatMessages(prev => [...prev, { role: 'assistant', content: `Error: ${e instanceof Error ? e.message : 'Failed to get response'}` }]);
    } finally {
      setChatLoading(false);
    }
  };

  const lines = result?.content.split('\n') ?? [];

  return (
    <div className="cicd-page animate-slide-up">
      {/* Header */}
      <div className="page-header">
        <div className="page-header__icon" style={{ background: 'rgba(139,92,246,0.15)', borderColor: 'rgba(139,92,246,0.3)', color: 'var(--accent-purple)' }}>
          <Zap size={20} />
        </div>
        <div>
          <h1 className="page-title">CI/CD Generator</h1>
          <p className="page-subtitle">Generate production-ready pipeline configs for your stack</p>
        </div>
      </div>

      {/* No repo warning */}
      {!scannedRepo && (
        <div className="no-repo-banner">
          <AlertTriangle size={16} />
          <span>Scan a repository first to generate a CI/CD config tailored to your stack.</span>
        </div>
      )}

      {/* Repo context */}
      {scannedRepo && (
        <div className="repo-context-bar">
          <div className="repo-context-item">
            <span className="repo-context-label">Repository</span>
            <span className="repo-context-value mono">{scannedRepo.owner}/{scannedRepo.repo}</span>
          </div>
          <div className="repo-context-divider" />
          <div className="repo-context-item">
            <span className="repo-context-label">Language</span>
            <span className="repo-context-value">{scannedRepo.language.primary}</span>
          </div>
          <div className="repo-context-divider" />
          <div className="repo-context-item">
            <span className="repo-context-label">Framework</span>
            <span className="repo-context-value">{scannedRepo.framework}</span>
          </div>
          <div className="repo-context-divider" />
          <div className="repo-context-item">
            <span className="repo-context-label">Package Manager</span>
            <span className="repo-context-value">{scannedRepo.package_manager}</span>
          </div>
        </div>
      )}

      {/* Platform Selector */}
      <div className="platform-section">
        <div className="section-label">Select CI/CD Platform</div>
        <div className="platform-grid">
          {PLATFORMS.map(p => (
            <button
              key={p.id}
              className={`platform-card ${selectedPlatform === p.id ? 'platform-card--selected' : ''}`}
              onClick={() => setSelectedPlatform(p.id)}
              style={{ '--platform-color': p.color } as React.CSSProperties}
            >
              <div className="platform-card__icon" style={{ color: p.color }}>
                {p.icon}
              </div>
              <div className="platform-card__body">
                <div className="platform-card__name">{p.name}</div>
                <div className="platform-card__desc">{p.desc}</div>
              </div>
              {selectedPlatform === p.id && (
                <div className="platform-card__check">✓</div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* AI Mode Options */}
      <div className="ai-options-section">
        <label className="ai-toggle">
          <input 
            type="checkbox" 
            checked={useAi} 
            onChange={(e) => setUseAi(e.target.checked)} 
          />
          <span className="ai-toggle-text">Enable AI-Powered Generation (Groq/OpenAI)</span>
          <span className="ai-badge">PRO</span>
        </label>

        {useAi && (
          <div className="ai-settings-grid animate-fade-in">
            <div className="ai-input-group">
              <label>API Key</label>
              <input 
                type="password" 
                value={aiConfig.api_key} 
                onChange={(e) => setAiConfig({...aiConfig, api_key: e.target.value})}
                placeholder="gsk_..."
              />
            </div>
            <div className="ai-input-group">
              <label>Model</label>
              <input 
                type="text" 
                value={aiConfig.model} 
                onChange={(e) => setAiConfig({...aiConfig, model: e.target.value})}
                placeholder="openai/gpt-oss-120b"
              />
            </div>
            
            <div className="ai-input-group">
              <label>Target Cloud</label>
              <select value={targetCloud} onChange={(e) => setTargetCloud(e.target.value)}>
                <option value="AWS">AWS</option>
                <option value="GCP">GCP</option>
                <option value="Azure">Azure</option>
                <option value="Self-Hosted">Self-Hosted</option>
              </select>
            </div>
            
            <div className="ai-input-group">
              <label>Deployment Strategy</label>
              <select value={deploymentStrategy} onChange={(e) => setDeploymentStrategy(e.target.value)}>
                <option value="EC2/VM">EC2 / VM</option>
                <option value="Docker/Container">Docker / Container</option>
                <option value="Serverless">Serverless</option>
                <option value="Kubernetes">Kubernetes</option>
                <option value="On-Premise">On-Premise</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Generate Button */}
      <button
        className={`generate-btn ${loading ? 'generate-btn--loading' : ''} ${useAi ? 'generate-btn--ai' : ''}`}
        onClick={handleGenerate}
        disabled={loading || !scannedRepo}
      >
        {loading ? (
          <>
            <span className={`spinner ${useAi ? 'spinner--white' : 'spinner--purple'}`} />
            {useAi ? 'AI is Thinking...' : 'Generating Pipeline...'}
          </>
        ) : (
          <>
            <Zap size={15} />
            Generate {PLATFORMS.find(p => p.id === selectedPlatform)?.name} {useAi ? 'with AI' : 'Config'}
          </>
        )}
      </button>

      {error && (
        <div className="error-banner animate-fade-in">
          <AlertTriangle size={15} />
          <span>{error}</span>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="result-section animate-slide-up">
          {/* Result Header */}
          <div className="result-header">
            <div className="result-header__left">
              <div className="result-file-badge">
                <span className="mono">{result.filename}</span>
              </div>
              <div className="result-meta-chips">
                <span className="result-meta-chip">{result.language}</span>
                <span className="result-meta-chip">{result.framework}</span>
                <span className="result-meta-chip">{lines.length} lines</span>
              </div>
            </div>
            <div className="result-header__actions">
              <button
                className="action-btn"
                onClick={() => setShowRaw(!showRaw)}
              >
                {showRaw ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                {showRaw ? 'Hide Raw' : 'Show Raw'}
              </button>
              <button className="action-btn action-btn--copy" onClick={handleCopy}>
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
              <button className="action-btn action-btn--download" onClick={handleDownload}>
                <Download size={14} />
                Download
              </button>
            </div>
          </div>

          {/* Code Viewer */}
          <div className="code-viewer">
            <div className="code-viewer__header">
              <div className="code-viewer__dots">
                <span /><span /><span />
              </div>
              <span className="code-viewer__title mono">{result.filename}</span>
            </div>
            <div className="code-viewer__body">
              <pre className="code-content">
                {lines.map((line, i) => (
                  <div key={i} className="code-line">
                    <span className="code-line-number">{i + 1}</span>
                    <span className="code-line-content">{highlightLine(line)}</span>
                  </div>
                ))}
              </pre>
            </div>
          </div>

          {/* AI Implementation Guide */}
          {result.instructions && (
            <div className="implementation-guide-section">
              <div className="section-label" style={{ marginTop: '24px', color: 'var(--accent-purple)' }}>
                <Zap size={14} style={{ display: 'inline', marginRight: '6px' }} />
                AI Implementation Guide
              </div>
              <div className="guide-content" style={{
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid var(--border-soft)',
                borderRadius: 'var(--radius-lg)',
                padding: '24px',
                marginTop: '12px',
                fontSize: '0.95rem',
                lineHeight: '1.6',
                color: 'var(--text-secondary)'
              }}>
                <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                  {result.instructions}
                </pre>
              </div>
            </div>
          )}

          {/* Feature List */}
          <div className="features-list">
            <div className="section-label">What's included</div>
            <div className="features-grid">
              {getFeatures(result.platform, scannedRepo).map(f => (
                <div key={f} className="feature-item">
                  <span className="feature-check">✓</span>
                  <span>{f}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}\n
      {/* Inline Pipeline Chat — ChatGPT Style */}
      {result && (
        <div className="inline-chat-section animate-slide-up">
          {/* Divider */}
          <div className="inline-chat-header">
            <div className="inline-chat-header__line" />
            <div className="inline-chat-header__label">
              <MessageSquare size={14} />
              Pipeline Assistant
            </div>
            <div className="inline-chat-header__line" />
          </div>

          {/* Chat Title */}
          <div className="inline-chat-title">
            Ask anything about your generated pipeline
          </div>
          <div className="inline-chat-subtitle">
            Got errors? Need changes? Ask the AI — it knows your full {PLATFORMS.find(p => p.id === selectedPlatform)?.name} pipeline.
          </div>

          {/* Conversation History */}
          {chatMessages.length > 0 && (
            <div className="inline-chat-history">
              {chatMessages.map((msg, i) => (
                <div key={i} className={`inline-chat-msg inline-chat-msg--${msg.role}`}>
                  <div className="inline-chat-msg__avatar">
                    {msg.role === 'user' ? '👤' : '🤖'}
                  </div>
                  <div className="inline-chat-msg__body">
                    <div className="inline-chat-msg__role">{msg.role === 'user' ? 'You' : 'Pipeline AI'}</div>
                    <div className="inline-chat-msg__text">{msg.content}</div>
                  </div>
                </div>
              ))}
              {chatLoading && (
                <div className="inline-chat-msg inline-chat-msg--assistant">
                  <div className="inline-chat-msg__avatar">🤖</div>
                  <div className="inline-chat-msg__body">
                    <div className="inline-chat-msg__role">Pipeline AI</div>
                    <div className="inline-chat-msg__text inline-chat-typing">
                      <span /><span /><span />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Input Box — ChatGPT Style */}
          <form className="inline-chat-form" onSubmit={handleChat}>
            <div className="inline-chat-input-wrap">
              <button type="button" className="inline-chat-plus" title="Attach context">
                <X size={16} style={{ transform: 'rotate(45deg)' }} />
              </button>
              <input
                type="text"
                className="inline-chat-input"
                placeholder="Ask anything about your pipeline..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={chatLoading}
                autoComplete="off"
              />
              <button
                type="submit"
                className={`inline-chat-send ${chatInput.trim() ? 'inline-chat-send--active' : ''}`}
                disabled={chatLoading || !chatInput.trim()}
                title="Send"
              >
                <Send size={16} />
              </button>
            </div>
            <div className="inline-chat-hint">Pipeline AI can make mistakes. Verify critical changes.</div>
          </form>
        </div>
      )}
    </div>
  );
}

function highlightLine(line: string): React.ReactNode {
  // Simple YAML/Groovy syntax highlighting
  if (line.trimStart().startsWith('#')) {
    return <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>{line}</span>;
  }
  if (line.includes(':') && !line.trimStart().startsWith('-')) {
    const colonIdx = line.indexOf(':');
    const key = line.substring(0, colonIdx + 1);
    const val = line.substring(colonIdx + 1);
    return (
      <>
        <span style={{ color: 'var(--accent-cyan)' }}>{key}</span>
        <span style={{ color: 'var(--text-primary)' }}>{val}</span>
      </>
    );
  }
  if (line.trimStart().startsWith('-')) {
    return <span style={{ color: 'var(--accent-green)' }}>{line}</span>;
  }
  if (line.includes('stage') || line.includes('job') || line.includes('step')) {
    return <span style={{ color: 'var(--accent-yellow)' }}>{line}</span>;
  }
  return <span style={{ color: 'var(--text-primary)' }}>{line}</span>;
}

function getFeatures(platform: string, repo: RepoScanResult | null): string[] {
  const base = [
    'Dependency installation with caching',
    'Code linting & style checks',
    repo?.metadata.has_tests ? 'Test execution with coverage reporting' : 'Build verification',
    'Security vulnerability scanning (Trivy)',
    'Build artifact archiving',
  ];
  if (platform === 'github_actions') {
    base.push('Matrix build strategy', 'SARIF security report upload', 'Workflow dispatch trigger');
    if (repo?.metadata.has_dockerfile) base.push('Docker build & push to GHCR');
  }
  if (platform === 'jenkins') {
    base.push('Build discard policy', 'Concurrent build prevention', 'Email notifications on failure');
    if (repo?.metadata.has_dockerfile) base.push('Docker image build & registry push');
  }
  if (platform === 'gitlab_ci') {
    base.push('Merge request pipelines', 'Workflow rules', 'GitLab Container Registry integration');
  }
  return base;
}
