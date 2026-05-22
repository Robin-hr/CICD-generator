import httpx
import base64
import re
from typing import Optional, Dict, Any
import json


LANGUAGE_MAP = {
    "py": "Python", "js": "JavaScript", "ts": "TypeScript", "jsx": "JavaScript",
    "tsx": "TypeScript", "java": "Java", "go": "Go", "rs": "Rust",
    "rb": "Ruby", "php": "PHP", "cs": "C#", "cpp": "C++", "c": "C",
    "kt": "Kotlin", "swift": "Swift", "scala": "Scala", "ex": "Elixir",
}

FRAMEWORK_INDICATORS = {
    "Python": {
        "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
        "tornado": "Tornado", "sanic": "Sanic", "aiohttp": "aiohttp",
        "starlette": "Starlette", "pyramid": "Pyramid",
    },
    "JavaScript": {
        "react": "React", "vue": "Vue.js", "angular": "@angular/core",
        "express": "Express.js", "next": "Next.js", "nuxt": "Nuxt.js",
        "svelte": "Svelte", "nestjs": "@nestjs/core", "gatsby": "Gatsby",
    },
    "TypeScript": {
        "react": "React", "vue": "Vue.js", "angular": "@angular/core",
        "express": "Express.js", "next": "Next.js", "nestjs": "@nestjs/core",
    },
    "Java": {
        "spring": "Spring Boot", "quarkus": "Quarkus", "micronaut": "Micronaut",
        "jakarta": "Jakarta EE",
    },
    "Go": {
        "gin": "Gin", "echo": "Echo", "fiber": "Fiber", "chi": "Chi",
    },
    "Ruby": {
        "rails": "Ruby on Rails", "sinatra": "Sinatra",
    },
}

PACKAGE_MANAGERS = {
    "package.json": "npm/yarn", "yarn.lock": "Yarn", "package-lock.json": "npm",
    "pnpm-lock.yaml": "pnpm", "requirements.txt": "pip", "Pipfile": "Pipenv",
    "pyproject.toml": "Poetry/pip", "poetry.lock": "Poetry",
    "go.mod": "Go Modules", "Cargo.toml": "Cargo",
    "pom.xml": "Maven", "build.gradle": "Gradle",
    "Gemfile": "Bundler", "composer.json": "Composer",
}

DEPLOYMENT_INDICATORS = {
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "helm": "Helm",
    ".github/workflows": "GitHub Actions",
    "Jenkinsfile": "Jenkins",
    ".gitlab-ci.yml": "GitLab CI",
    "serverless.yml": "Serverless Framework",
    "vercel.json": "Vercel",
    "netlify.toml": "Netlify",
    "heroku.yml": "Heroku",
    "app.yaml": "Google App Engine",
    "Procfile": "Heroku/Process-based",
}


class RepoScanner:
    def __init__(self, github_token: Optional[str] = None):
        self.token = github_token
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"

    def parse_repo_url(self, url: str):
        patterns = [
            r"github\.com[:/]([^/]+)/([^/\s.]+?)(?:\.git)?$",
        ]
        url = url.strip().rstrip("/")
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2)
        raise ValueError(f"Invalid GitHub URL: {url}")

    async def fetch_tree(self, owner: str, repo: str) -> list:
        async with httpx.AsyncClient(timeout=30) as client:
            # Get default branch
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers=self.headers
            )
            if resp.status_code == 404:
                raise ValueError(f"Repository not found: {owner}/{repo}")
            if resp.status_code == 403:
                raise ValueError("Rate limit exceeded. Provide a GitHub token.")
            resp.raise_for_status()
            repo_data = resp.json()
            default_branch = repo_data.get("default_branch", "main")

            # Get file tree
            tree_resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1",
                headers=self.headers
            )
            tree_resp.raise_for_status()
            tree_data = tree_resp.json()
            return tree_data.get("tree", []), repo_data

    async def fetch_file(self, owner: str, repo: str, path: str) -> Optional[str]:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                headers=self.headers
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            if data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            return data.get("content", "")

    def detect_language(self, files: list) -> Dict[str, Any]:
        lang_count: Dict[str, int] = {}
        for f in files:
            if f.get("type") != "blob":
                continue
            path = f["path"]
            ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
            lang = LANGUAGE_MAP.get(ext)
            if lang:
                lang_count[lang] = lang_count.get(lang, 0) + 1

        if not lang_count:
            return {"primary": "Unknown", "all": {}}

        primary = max(lang_count, key=lang_count.get)
        total = sum(lang_count.values())
        percentages = {k: round(v / total * 100, 1) for k, v in lang_count.items()}
        return {"primary": primary, "all": percentages}

    def detect_package_manager(self, file_paths: set) -> str:
        for filename, pm in PACKAGE_MANAGERS.items():
            if any(filename in p for p in file_paths):
                return pm
        return "Unknown"

    def detect_framework(self, language: str, file_paths: set, file_contents: Dict[str, str]) -> str:
        frameworks = FRAMEWORK_INDICATORS.get(language, {})
        
        # Check package.json for JS/TS
        for pkg_file in ["package.json", "requirements.txt", "pyproject.toml", "Pipfile", "go.mod", "pom.xml", "Gemfile"]:
            content = file_contents.get(pkg_file, "")
            if content:
                for key, framework_name in frameworks.items():
                    if key.lower() in content.lower():
                        return framework_name
        
        # Check file structure
        for path in file_paths:
            for key, framework_name in frameworks.items():
                if key.lower() in path.lower():
                    return framework_name
        
        return "None detected"

    def detect_deployment(self, file_paths: set) -> list:
        detected = []
        for indicator, deployment_type in DEPLOYMENT_INDICATORS.items():
            if any(indicator.lower() in p.lower() for p in file_paths):
                if deployment_type not in detected:
                    detected.append(deployment_type)
        return detected if detected else ["None detected"]

    def detect_test_framework(self, language: str, file_paths: set) -> str:
        test_frameworks = {
            "Python": {"pytest": "pytest", "unittest": "unittest", "nose": "nose"},
            "JavaScript": {"jest": "Jest", "mocha": "Mocha", "vitest": "Vitest", "cypress": "Cypress"},
            "TypeScript": {"jest": "Jest", "mocha": "Mocha", "vitest": "Vitest"},
            "Java": {"junit": "JUnit", "testng": "TestNG"},
            "Go": {"testing": "Go Testing"},
            "Ruby": {"rspec": "RSpec", "minitest": "Minitest"},
        }
        
        frameworks = test_frameworks.get(language, {})
        for path in file_paths:
            for key, name in frameworks.items():
                if key in path.lower():
                    return name
        
        # Check for test directories
        test_dirs = [p for p in file_paths if "test" in p.lower() or "spec" in p.lower()]
        if test_dirs:
            return list(frameworks.values())[0] if frameworks else "Custom"
        
        return "None detected"

    async def scan(self, repo_url: str) -> dict:
        owner, repo = self.parse_repo_url(repo_url)
        tree, repo_data = await self.fetch_tree(owner, repo)

        file_paths = {f["path"] for f in tree if f.get("type") == "blob"}
        
        # Fetch key config and IaC files
        key_files = [
            "package.json", "requirements.txt", "pyproject.toml", "Pipfile", 
            "go.mod", "pom.xml", "build.gradle", "Gemfile", "Cargo.toml",
            "main.tf", "variables.tf", "outputs.tf", "terraform.tfvars",
            "docker-compose.yml", "docker-compose.yaml", "k8s.yaml", "deployment.yaml"
        ]
        # Also include any .tf files
        tf_files = [p for p in file_paths if p.endswith(".tf")][:5]
        key_files.extend(tf_files)
        
        file_contents = {}
        for kf in key_files:
            if kf in file_paths:
                content = await self.fetch_file(owner, repo, kf)
                if content:
                    file_contents[kf] = content

        lang_info = self.detect_language(tree)
        primary_lang = lang_info["primary"]
        package_manager = self.detect_package_manager(file_paths)
        framework = self.detect_framework(primary_lang, file_paths, file_contents)
        deployment = self.detect_deployment(file_paths)
        test_framework = self.detect_test_framework(primary_lang, file_paths)

        # Repo metadata
        total_files = len([f for f in tree if f.get("type") == "blob"])
        has_dockerfile = any("Dockerfile" in p for p in file_paths)
        has_ci = any(".github/workflows" in p or ".gitlab-ci" in p or "Jenkinsfile" in p for p in file_paths)
        has_tests = any("test" in p.lower() or "spec" in p.lower() for p in file_paths)

        # Deep Logic Detection
        logic_clues = []
        for path, content in file_contents.items():
            content_lower = content.lower()
            if "subprocess.run" in content or "os.system" in content:
                if "terraform" in content_lower: logic_clues.append(f"dynamic_terraform_in_{path}")
                if "aws" in content_lower: logic_clues.append(f"dynamic_aws_in_{path}")
            if "boto3" in content: logic_clues.append(f"boto3_usage_in_{path}")
            if "streamlit" in content: logic_clues.append(f"streamlit_app_in_{path}")
            if "fastapi" in content or "uvicorn" in content: logic_clues.append(f"fastapi_backend_in_{path}")
            
            # Detect port numbers
            import re
            port_matches = re.findall(r"port\s*=\s*(\d+)", content)
            for port in port_matches:
                logic_clues.append(f"detected_port_{port}_in_{path}")
            
            # Detect potential hardcoded keys
            if "access_key" in content_lower or "secret_key" in content_lower:
                if "=" in content and ('"' in content or "'" in content):
                    logic_clues.append(f"potential_hardcoded_secrets_in_{path}")

        # Detect Cloud Clues
        cloud_clues = []
        if any("aws" in p.lower() for p in file_paths): cloud_clues.append("aws")
        if any("gcp" in p.lower() or "google" in p.lower() for p in file_paths): cloud_clues.append("gcp")
        if any("azure" in p.lower() for p in file_paths): cloud_clues.append("azure")
        if any(p.endswith(".tf") for p in file_paths): cloud_clues.append("terraform")
        if any("docker-compose" in p.lower() for p in file_paths): cloud_clues.append("docker-compose")

        return {
            "owner": owner,
            "repo": repo,
            "repo_url": repo_url,
            "description": repo_data.get("description", ""),
            "default_branch": repo_data.get("default_branch", "main"),
            "stars": repo_data.get("stargazers_count", 0),
            "language": {"primary": repo_data.get("language", "Unknown"), "all": lang_info["all"]},
            "framework": framework,
            "package_manager": package_manager,
            "deployment_styles": deployment,
            "test_framework": test_framework,
            "metadata": {
                "total_files": len(tree),
                "has_dockerfile": has_dockerfile,
                "has_ci": has_ci,
                "has_tests": has_tests,
                "private": repo_data.get("private", False),
                "topics": repo_data.get("topics", []),
                "cloud_clues": cloud_clues,
                "logic_clues": logic_clues
            },
            "file_tree_sample": [f["path"] for f in tree if f.get("type") == "blob"][:100],
            "file_contents": file_contents,
        }
