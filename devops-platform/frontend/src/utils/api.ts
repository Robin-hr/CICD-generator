const BASE_URL = 'http://localhost:8000';

export interface RepoScanResult {
  owner: string;
  repo: string;
  repo_url: string;
  description: string;
  default_branch: string;
  stars: number;
  language: { primary: string; all: Record<string, number> };
  framework: string;
  package_manager: string;
  deployment_styles: string[];
  test_framework: string;
  metadata: {
    total_files: number;
    has_dockerfile: boolean;
    has_ci: boolean;
    has_tests: boolean;
    private: boolean;
    topics: string[];
  };
  file_tree_sample: string[];
  file_tree_hierarchical: RepoNode[];
  structure_descriptions: Record<string, string>;
}

export interface RepoNode {
  name: string;
  type: 'blob' | 'tree' | 'dir';
  path: string;
  children?: RepoNode[];
}

export interface CICDResult {
  platform: string;
  filename: string;
  content: string;
  instructions?: string;
  language: string;
  framework: string;
}

export async function scanRepo(repoUrl: string, githubToken?: string): Promise<RepoScanResult> {
  const res = await fetch(`${BASE_URL}/api/scan/repo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl, github_token: githubToken || undefined }),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.detail || 'Scan failed');
  return json.data;
}

export async function generateCICD(
  repoInfo: RepoScanResult, 
  platform: string, 
  useAi: boolean = false, 
  aiConfig: any = {},
  targetCloud: string = 'AWS',
  deploymentStrategy: string = 'Serverless'
): Promise<CICDResult> {
  const res = await fetch(`${BASE_URL}/api/generate/cicd`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      repo_info: repoInfo, 
      platform,
      use_ai: useAi,
      ai_config: aiConfig,
      target_cloud: targetCloud,
      deployment_strategy: deploymentStrategy
    }),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.detail || 'Generation failed');
  return json.data;
}

export async function chatPipeline(
  pipelineCode: string,
  userMessage: string,
  repoInfo: RepoScanResult,
  platform: string,
  aiConfig: any = {}
): Promise<string> {
  const res = await fetch(`${BASE_URL}/api/chat/pipeline`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pipeline_code: pipelineCode,
      user_message: userMessage,
      repo_info: repoInfo,
      platform,
      ai_config: aiConfig,
    }),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.detail || 'Chat failed');
  return json.data;
}
