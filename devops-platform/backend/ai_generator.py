import json
import httpx
from typing import Dict, Any, Optional
from openai import OpenAI, AsyncOpenAI

class AIGenerator:
    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None):
        if not api_key:
            raise ValueError("API key is required for AI generation.")
        
        # Determine base_url based on key or model if not provided
        if not base_url:
            if api_key.startswith("gsk_"):
                base_url = "https://api.groq.com/openai/v1"
            elif "openai" in model.lower():
                base_url = "https://api.openai.com/v1"
            # Add more defaults as needed
            
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.base_url = base_url

    async def generate(self, repo_info: dict, platform: str, file_contents: Dict[str, str] = {}, 
                       target_cloud: str = "AWS", deployment_strategy: str = "Serverless",
                       hierarchical_tree: Optional[list] = None, 
                       structure_descriptions: Optional[dict] = None) -> dict:
        prompt = self._build_prompt(
            repo_info, platform, file_contents, target_cloud, 
            deployment_strategy, hierarchical_tree, structure_descriptions
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert DevOps engineer specializing in CI/CD pipelines. Generate perfect, production-ready configuration files."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )
            
            content = response.choices[0].message.content
            yaml_content = content
            instructions = ""
            
            if "```yaml" in content:
                yaml_content = content.split("```yaml")[1].split("```")[0].strip()
            elif "```json" in content:
                yaml_content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                yaml_content = content.split("```")[1].split("```")[0].strip()
            
            if "```markdown" in content:
                instructions = content.split("```markdown")[1].split("```")[0].strip()
            elif "### Implementation Guide" in content:
                # Fallback if AI forgot markdown block
                parts = content.split("### Implementation Guide")
                if len(parts) > 1:
                    instructions = "### Implementation Guide" + parts[1]
            
            return {
                "platform": platform,
                "filename": self._get_filename(platform),
                "content": yaml_content,
                "instructions": instructions,
                "language": repo_info.get("language", {}).get("primary", "Unknown"),
                "framework": repo_info.get("framework", "Unknown"),
                "method": "AI"
            }
        except Exception as e:
            raise Exception(f"AI Generation failed: {str(e)}")

    def _get_filename(self, platform: str) -> str:
        return {
            "github_actions": ".github/workflows/ci-cd.yml",
            "jenkins": "Jenkinsfile",
            "gitlab_ci": ".gitlab-ci.yml",
        }.get(platform, "cicd_config")

    def _build_prompt(self, repo_info: dict, platform: str, file_contents: Dict[str, str], 
                     target_cloud: str, deployment_strategy: str,
                     hierarchical_tree: Optional[list] = None,
                     structure_descriptions: Optional[dict] = None) -> str:
        metadata = {
            "owner": repo_info.get("owner"),
            "repo": repo_info.get("repo"),
            "primary_language": repo_info.get("language", {}).get("primary"),
            "all_languages": repo_info.get("language", {}).get("all"),
            "framework": repo_info.get("framework"),
            "package_manager": repo_info.get("package_manager"),
            "test_framework": repo_info.get("test_framework"),
            "deployment_styles": repo_info.get("deployment_styles"),
            "has_dockerfile": repo_info.get("metadata", {}).get("has_dockerfile"),
            "has_tests": repo_info.get("metadata", {}).get("has_tests"),
        }

        files_context = "\n".join([f"--- FILE: {path} ---\n{content[:2000]}" for path, content in file_contents.items()])

        # Base Directives
        prompt = f"""
Generate a high-quality, production-ready CI/CD pipeline configuration file for the following repository.

Platform: {platform}
Repository Metadata: 
{json.dumps(metadata, indent=2)}

Deployment Intent (MANDATORY):
- Target Cloud: {target_cloud}
- Deployment Strategy: {deployment_strategy}

Key Files Content:
{files_context}

Repository Structure (HIERARCHICAL):
{json.dumps(hierarchical_tree, indent=2) if hierarchical_tree else "Not provided"}

Structure Descriptions:
{json.dumps(structure_descriptions, indent=2) if structure_descriptions else "Not provided"}

Core Directives for "Directly Runnable" Perfection:
1. **Zero-Edit Policy**: The generated code must be syntactically perfect and logically sound for {platform}.
2. **Contextual Intelligence**: Use the hierarchical tree and descriptions to determine the EXACT entry point (e.g., `uvicorn backend.main:app` if `main.py` is in `backend/`).
3. **S3 Static Hosting (If Strategy is S3)**:
    - Use `aws s3 sync` to upload the build folder (e.g., `dist`, `build`, `out`) to the S3 bucket.
    - MUST include a CloudFront invalidation step if the target cloud is AWS.
    - Set `bucket_name` and `cloudfront_id` as env/secrets placeholders.
4. **EC2 Deployment Reliability (If Strategy is EC2)**:
    - **Safe Paths**: Use `/home/${{{{ secrets.SSH_USERNAME }}}}/app` instead of `/app`.
    - **System Packages**: Ensure `unzip`, `python3-pip`, and `curl` are installed via `sudo yum/apt install`.
    - **Health Checks**: Append a health check step using `curl -f http://...` with retries.
5. **Node.js Safety**: Check for `package-lock.json`, `yarn.lock`, or `pnpm-lock.yaml` before choosing the install command. Fallback to `npm install` if no lock file is found.
6. **Sequence**: If `dynamic_terraform` clues are found, you MUST install and setup Terraform BEFORE starting any app code.
"""

        # Platform Specific Directives
        if platform == "github_actions":
            prompt += f"""
5. **Absolute Zero-Defect Enterprise Execution (GitHub Actions)**:
    - **OIDC**: You MUST use `permissions: {{ id-token: write, contents: read }}` and `aws-actions/configure-aws-credentials@v4` for AWS.
    - **Caching**: Use dependency caching (e.g., `actions/setup-python@v5` with `cache: 'pip'`).
    - **Deployment Script**: Generate a ROBUST script based on the chosen strategy ({deployment_strategy}). 
    - **DO NOT** use generic hardcoded paths if the repo structure suggests otherwise.
    - **Entry point**: If {deployment_strategy} is EC2, identify if it's `main.py`, `app.py`, or a sub-module.
"""
        elif platform == "jenkins":
            prompt += f"""
5. **Absolute Zero-Defect Enterprise Execution (Jenkins)**:
    - Use declarative `pipeline {{ ... }}` syntax (Groovy).
    - **Global Env**: Define `environment {{ PATH = "$HOME/.local/bin:${{env.PATH}}" }}`.
    - **Security & Testing**: 
      - MUST include `Ruff`, `Pytest`, and `Checkov`.
      - **Trivy**: DO NOT use `pip`. Use `sh 'curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh && sudo mv bin/trivy /usr/local/bin/'`.
    - **Terraform Persistence**: `terraform init` MUST use `-backend-config` for production state.
    - **Terraform Flow**: MUST include `terraform validate`. For `apply`, use `cd EC2 && terraform apply -auto-approve tfplan` to avoid pathing errors.
    - **Dynamic Infrastructure**: Fetch IP via `script {{ env.SSH_HOST = sh(script: "terraform output -raw ec2_public_ip", returnStdout: true).trim() }}`.
    - **EC2 Deployment Stage**:
      - Package: `zip -r app.zip . -x "*.git*" "*venv*"`
      - Deploy: `sh "scp -o StrictHostKeyChecking=no app.zip ubuntu@$SSH_HOST:/app/"`
      - **Durable Service**: Mandatory `pkill` and durable uvicorn backgrounding (ideally generating/starting a systemd service file).
    - **Health Check Stage**: MUST verify via `curl -f http://$SSH_HOST:8000/docs` with a 10-retry loop.
"""
        elif platform == "gitlab_ci":
            prompt += f"""
5. **Absolute Zero-Defect Enterprise Execution (GitLab CI)**:
    - Use `.gitlab-ci.yml` standard syntax with strict stages (`scan`, `test`, `build`, `deploy`, `health`).
    - **Security & Testing**: 
      - MUST include `ruff`, `pytest`, and `checkov`.
      - **trivy**: MUST install via shell script: `curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh`.
    - **Terraform Flow**: Include `terraform validate`. For apply, use `cd EC2 && terraform apply -auto-approve tfplan`.
    - **Dynamic Infrastructure**: `export SSH_HOST=$(terraform output -raw ec2_public_ip)`.
    - **EC2 Deployment**:
      - Package: `zip -r app.zip . -x "*.git*" "*venv*"`
      - Deploy: `scp -o StrictHostKeyChecking=no app.zip $SSH_USER@$SSH_HOST:/app/`
      - **Durable SSH**: `ssh ... "cd /app && unzip -o app.zip && pip install -r requirements.txt && pkill -f uvicorn || true && nohup uvicorn main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &"`
    - **Health Check**: `curl -f http://$SSH_HOST:8000/docs` with a sequence loop.
"""

        # Final Formatting Instructions
        code_block_language = "groovy" if platform == "jenkins" else "yaml"
        prompt += f"""
Requirements for the pipeline: 
- Read carefully and apply EVERY directive perfectly.
- Output the pipeline configuration file content enclosed in ```{code_block_language} ... ```.
- IMMEDIATELY after the {code_block_language.upper()} block, output an Implementation Guide enclosed in ```markdown ... ```. This guide MUST explain exactly how to add this pipeline to the user's repository, what exact Secrets must be configured, and provide a brief walkthrough.
- Do NOT output any conversational text outside of these two code blocks.
"""
        return prompt

    async def chat(self, pipeline_code: str, user_message: str, repo_info: dict, platform: str) -> str:
        """Provides context-aware help regarding the generated pipeline code."""
        prompt = f"""
You are an expert DevOps engineer and CI/CD assistant.
A user has generated a {platform} pipeline using this tool and needs help or clarification.

### Context
- **Repository Metadata**: {json.dumps({k: v for k, v in repo_info.items() if k not in ['file_contents', 'file_tree_hierarchical', 'structure_descriptions']})}
- **Target Platform**: {platform}
- **Current Generated Pipeline Code**:
```{platform}
{pipeline_code}
```

### User Request
"{user_message}"

### Instructions
1. Provide a concise, professional, and helpful response.
2. If the user is reporting an error or logic failure, you MUST identify the cause, fix it, and output the ENTIRE corrected pipeline code in a ```{platform} block.
3. If the user asks for a change, explain how to modify the code or provide the updated snippet.
4. The goal is to make the pipeline "work perfectly" based on the user's feedback.
5. Do NOT output any unnecessary preamble. Focus on answering the user's specific query.
"""
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error communicating with AI: {str(e)}"

    async def analyze_structure(self, file_tree: list) -> Dict[str, str]:
        """Generates descriptions for key files and directories in the tree."""
        # We only pass a sample of the tree to keep the prompt small
        tree_str = "\n".join(file_tree[:100])
        prompt = f"""
Analyze the following repository file tree and provide a JSON mapping of path to a short (max 10 words) description of its purpose.
Focus on:
1. Root directories
2. Key configuration files (package.json, requirements.txt, etc.)
3. Main entry points (app.py, index.tsx, etc.)
4. Important scripts (Dockerfile, docker-compose.yml, train.py, etc.)

File Tree:
{tree_str}

Output ONLY a JSON object where keys are the paths and values are the descriptions.
Example: {{ "src/": "Frontend source code", "backend/main.py": "API entry point" }}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior DevOps architect. Analyze repo structures accurately."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" },
                temperature=0.1,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Structure analysis failed: {e}")
            return {}
