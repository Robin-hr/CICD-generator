from typing import Dict, Any, Optional


class CICDGenerator:
    def generate(self, repo_info: dict, platform: str, options: dict = {}) -> dict:
        generators = {
            "github_actions": self.generate_github_actions,
            "jenkins": self.generate_jenkinsfile,
            "gitlab_ci": self.generate_gitlab_ci,
        }
        if platform not in generators:
            raise ValueError(f"Unknown platform: {platform}. Choose from: {list(generators.keys())}")
        
        content = generators[platform](repo_info, options)
        return {
            "platform": platform,
            "filename": self._get_filename(platform),
            "content": content,
            "language": repo_info.get("language", {}).get("primary", "Unknown"),
            "framework": repo_info.get("framework", "Unknown"),
        }

    def _get_filename(self, platform: str) -> str:
        return {
            "github_actions": ".github/workflows/ci-cd.yml",
            "jenkins": "Jenkinsfile",
            "gitlab_ci": ".gitlab-ci.yml",
        }[platform]

    def _get_build_commands(self, lang: str, framework: str, pkg_manager: str) -> dict:
        commands = {
            "Python": {
                "install": self._python_install(pkg_manager),
                "lint": "flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics",
                "test": "pytest --cov=. --cov-report=xml -v",
                "build": "echo 'Python build complete'",
                "setup_version": "python-version: '3.11'",
            },
            "JavaScript": {
                "install": self._js_install(pkg_manager),
                "lint": f"{self._js_runner(pkg_manager)} lint" if "lint" in framework.lower() else f"{self._js_runner(pkg_manager)} run lint",
                "test": f"{self._js_runner(pkg_manager)} test -- --coverage --watchAll=false",
                "build": f"{self._js_runner(pkg_manager)} build",
                "setup_version": "node-version: '20'",
            },
            "TypeScript": {
                "install": self._js_install(pkg_manager),
                "lint": f"{self._js_runner(pkg_manager)} lint",
                "test": f"{self._js_runner(pkg_manager)} test -- --coverage --watchAll=false",
                "build": f"{self._js_runner(pkg_manager)} build",
                "setup_version": "node-version: '20'",
            },
            "Java": {
                "install": "echo 'Dependencies managed by Maven/Gradle'",
                "lint": "./mvnw checkstyle:check" if "maven" in pkg_manager.lower() else "./gradlew checkstyleMain",
                "test": "./mvnw test" if "maven" in pkg_manager.lower() else "./gradlew test",
                "build": "./mvnw package -DskipTests" if "maven" in pkg_manager.lower() else "./gradlew build -x test",
                "setup_version": "java-version: '17'",
            },
            "Go": {
                "install": "go mod download",
                "lint": "golangci-lint run ./...",
                "test": "go test -v -race -coverprofile=coverage.out ./...",
                "build": "go build -v ./...",
                "setup_version": "go-version: '1.21'",
            },
            "Ruby": {
                "install": "bundle install",
                "lint": "rubocop --parallel",
                "test": "bundle exec rspec",
                "build": "echo 'Ruby build complete'",
                "setup_version": "ruby-version: '3.2'",
            },
        }
        return commands.get(lang, {
            "install": "echo 'Install dependencies'",
            "lint": "echo 'Run linter'",
            "test": "echo 'Run tests'",
            "build": "echo 'Build project'",
            "setup_version": "",
        })

    def _python_install(self, pkg_manager: str) -> str:
        if "poetry" in pkg_manager.lower():
            return "pip install poetry && poetry install"
        if "pipenv" in pkg_manager.lower():
            return "pip install pipenv && pipenv install --dev"
        return "pip install -r requirements.txt"

    def _js_install(self, pkg_manager: str) -> str:
        if "pnpm" in pkg_manager.lower():
            return "pnpm install --frozen-lockfile"
        if "yarn" in pkg_manager.lower():
            return "yarn install --frozen-lockfile"
        return "npm ci"

    def _js_runner(self, pkg_manager: str) -> str:
        if "pnpm" in pkg_manager.lower():
            return "pnpm"
        if "yarn" in pkg_manager.lower():
            return "yarn"
        return "npm run"

    def _get_setup_step(self, lang: str, pkg_manager: str, version_str: str) -> str:
        if lang == "Python":
            return f"""      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          {version_str}"""
        elif lang in ["JavaScript", "TypeScript"]:
            setup = f"""      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          {version_str}
          cache: '{self._cache_type(pkg_manager)}'"""
            if "pnpm" in pkg_manager.lower():
                setup = f"""      - name: Set up pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 8
\n""" + setup
            return setup
        elif lang == "Java":
            return f"""      - name: Set up JDK
        uses: actions/setup-java@v4
        with:
          {version_str}
          distribution: 'temurin'
          cache: 'maven'"""
        elif lang == "Go":
            return f"""      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          {version_str}"""
        elif lang == "Ruby":
            return f"""      - name: Set up Ruby
        uses: ruby/setup-ruby@v1
        with:
          {version_str}
          bundler-cache: true"""
        return ""

    def _cache_type(self, pkg_manager: str) -> str:
        if "pnpm" in pkg_manager.lower():
            return "pnpm"
        if "yarn" in pkg_manager.lower():
            return "yarn"
        return "npm"

    def generate_github_actions(self, repo_info: dict, options: dict) -> str:
        lang = repo_info.get("language", {}).get("primary", "Unknown")
        framework = repo_info.get("framework", "Unknown")
        pkg_manager = repo_info.get("package_manager", "Unknown")
        branch = repo_info.get("default_branch", "main")
        has_docker = repo_info.get("metadata", {}).get("has_dockerfile", False)
        has_tests = repo_info.get("metadata", {}).get("has_tests", True)

        cmds = self._get_build_commands(lang, framework, pkg_manager)
        setup_step = self._get_setup_step(lang, pkg_manager, cmds["setup_version"])

        test_job = ""
        if has_tests:
            test_job = f"""
      - name: Run Tests
        run: {cmds['test']}

      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        if: always()
        with:
          files: ./coverage.xml,./coverage.out
          fail_ci_if_error: false
"""

        docker_job = ""
        if has_docker:
            owner = repo_info.get("owner", "owner").lower()
            repo = repo_info.get("repo", "app").lower()
            docker_job = f"""
  docker:
    name: Build & Push Docker Image
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/{branch}'
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/{owner}/{repo}
          tags: |
            type=sha,prefix=sha-
            type=ref,event=branch
            type=semver,pattern={{{{version}}}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{{{ steps.meta.outputs.tags }}}}
          labels: ${{{{ steps.meta.outputs.labels }}}}
          cache-from: type=gha
          cache-to: type=gha,mode=max
"""

        return f"""# CI/CD Pipeline for {repo_info.get('repo', 'app')}
# Generated by DevOps Platform
# Language: {lang} | Framework: {framework} | Package Manager: {pkg_manager}

name: CI/CD Pipeline

on:
  push:
    branches: [ "{branch}", "develop" ]
  pull_request:
    branches: [ "{branch}" ]
  workflow_dispatch:

env:
  NODE_ENV: test

jobs:
  build:
    name: Build & Test
    runs-on: ubuntu-latest

    strategy:
      matrix:
        os: [ubuntu-latest]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

{setup_step}

      - name: Install dependencies
        run: {cmds['install']}

      - name: Lint code
        run: {cmds['lint']}
        continue-on-error: true
{test_job}
      - name: Build project
        run: {cmds['build']}

      - name: Archive build artifacts
        uses: actions/upload-artifact@v4
        if: success()
        with:
          name: build-artifacts
          path: |
            dist/
            build/
            target/
          retention-days: 7
{docker_job}
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'

  notify:
    name: Notify
    runs-on: ubuntu-latest
    needs: [build, security]
    if: always()
    steps:
      - name: Pipeline Status
        run: |
          echo "Pipeline completed for ${{{{ github.repository }}}}"
          echo "Commit: ${{{{ github.sha }}}}"
          echo "Branch: ${{{{ github.ref_name }}}}"
          echo "Status: ${{{{ job.status }}}}"
"""

    def generate_jenkinsfile(self, repo_info: dict, options: dict) -> str:
        lang = repo_info.get("language", {}).get("primary", "Unknown")
        framework = repo_info.get("framework", "Unknown")
        pkg_manager = repo_info.get("package_manager", "Unknown")
        has_docker = repo_info.get("metadata", {}).get("has_dockerfile", False)
        has_tests = repo_info.get("metadata", {}).get("has_tests", True)
        repo_name = repo_info.get("repo", "app")

        cmds = self._get_build_commands(lang, framework, pkg_manager)

        agent_block = "agent any"
        tool_block = ""
        if lang == "Java":
            tool_block = """
    tools {
        jdk 'JDK-17'
        maven 'Maven-3.9'
    }"""
        elif lang in ["JavaScript", "TypeScript"]:
            tool_block = """
    tools {
        nodejs 'NodeJS-20'
    }"""

        test_stage = ""
        if has_tests:
            test_stage = f"""
        stage('Test') {{
            steps {{
                sh '{cmds["test"]}'
            }}
            post {{
                always {{
                    publishTestResults testResultsPattern: '**/test-results/*.xml'
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')]
                }}
            }}
        }}"""

        docker_stage = ""
        if has_docker:
            docker_stage = f"""
        stage('Docker Build & Push') {{
            when {{
                branch 'main'
            }}
            steps {{
                script {{
                    def image = docker.build("{repo_name.lower()}:${{BUILD_NUMBER}}")
                    docker.withRegistry('https://registry.hub.docker.com', 'dockerhub-credentials') {{
                        image.push()
                        image.push('latest')
                    }}
                }}
            }}
        }}"""

        return f"""// Jenkinsfile for {repo_name}
// Generated by DevOps Platform
// Language: {lang} | Framework: {framework}

pipeline {{
    {agent_block}
{tool_block}

    environment {{
        APP_NAME = '{repo_name}'
        BUILD_VERSION = "${{BUILD_NUMBER}}"
        GIT_COMMIT_SHORT = "${{GIT_COMMIT[0..7]}}"
    }}

    options {{
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
        disableConcurrentBuilds()
    }}

    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
                sh 'git log --oneline -5'
            }}
        }}

        stage('Install Dependencies') {{
            steps {{
                sh '{cmds["install"]}'
            }}
        }}

        stage('Lint') {{
            steps {{
                sh '{cmds["lint"]}'
            }}
        }}
{test_stage}

        stage('Build') {{
            steps {{
                sh '{cmds["build"]}'
            }}
        }}

        stage('Security Scan') {{
            steps {{
                sh '''
                    if command -v trivy &> /dev/null; then
                        trivy fs --exit-code 0 --severity HIGH,CRITICAL .
                    else
                        echo "Trivy not installed, skipping security scan"
                    fi
                '''
            }}
        }}
{docker_stage}

        stage('Archive Artifacts') {{
            steps {{
                archiveArtifacts artifacts: 'dist/**, build/**, target/*.jar', fingerprint: true, allowEmptyArchive: true
            }}
        }}
    }}

    post {{
        always {{
            cleanWs()
            echo "Pipeline finished: ${{currentBuild.result}}"
        }}
        success {{
            echo "✅ Pipeline succeeded for ${{APP_NAME}} build #${{BUILD_NUMBER}}"
        }}
        failure {{
            echo "❌ Pipeline failed for ${{APP_NAME}} build #${{BUILD_NUMBER}}"
            mail to: '${{env.CHANGE_AUTHOR_EMAIL}}',
                 subject: "Build Failed: ${{APP_NAME}} #${{BUILD_NUMBER}}",
                 body: "Check Jenkins: ${{BUILD_URL}}"
        }}
        unstable {{
            echo "⚠️ Pipeline unstable for ${{APP_NAME}}"
        }}
    }}
}}
"""

    def generate_gitlab_ci(self, repo_info: dict, options: dict) -> str:
        lang = repo_info.get("language", {}).get("primary", "Unknown")
        framework = repo_info.get("framework", "Unknown")
        pkg_manager = repo_info.get("package_manager", "Unknown")
        branch = repo_info.get("default_branch", "main")
        has_docker = repo_info.get("metadata", {}).get("has_dockerfile", False)
        has_tests = repo_info.get("metadata", {}).get("has_tests", True)
        repo_name = repo_info.get("repo", "app")

        cmds = self._get_build_commands(lang, framework, pkg_manager)

        image_map = {
            "Python": "python:3.11-slim",
            "JavaScript": "node:20-alpine",
            "TypeScript": "node:20-alpine",
            "Java": "maven:3.9-eclipse-temurin-17",
            "Go": "golang:1.21-alpine",
            "Ruby": "ruby:3.2-alpine",
        }
        base_image = image_map.get(lang, "ubuntu:22.04")

        cache_config = ""
        if lang in ["JavaScript", "TypeScript"]:
            cache_config = """cache:
  paths:
    - node_modules/
  key:
    files:
      - package-lock.json
      - yarn.lock"""
        elif lang == "Python":
            cache_config = """cache:
  paths:
    - .pip-cache/
    - venv/
  key: "$CI_COMMIT_REF_SLUG-python"
"""

        test_job = ""
        if has_tests:
            test_job = f"""
test:
  stage: test
  script:
    - {cmds['test']}
  coverage: '/TOTAL.*\\s+(\\d+%)$/'
  artifacts:
    when: always
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
      junit: test-results.xml
    expire_in: 1 week
"""

        docker_job = ""
        if has_docker:
            docker_job = f"""
docker-build:
  stage: deploy
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" $CI_REGISTRY
  script:
    - docker build --pull -t "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA" .
    - docker tag "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA" "$CI_REGISTRY_IMAGE:latest"
    - docker push "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
    - docker push "$CI_REGISTRY_IMAGE:latest"
  only:
    - {branch}
"""

        return f"""# GitLab CI/CD Pipeline for {repo_name}
# Generated by DevOps Platform
# Language: {lang} | Framework: {framework} | Package Manager: {pkg_manager}

image: {base_image}

stages:
  - install
  - lint
  - test
  - build
  - security
  - deploy

variables:
  APP_NAME: "{repo_name}"
  GIT_DEPTH: "10"

{cache_config}

install:
  stage: install
  script:
    - {cmds['install']}
  artifacts:
    paths:
      - node_modules/
      - venv/
      - vendor/
    expire_in: 1 hour

lint:
  stage: lint
  script:
    - {cmds['lint']}
  allow_failure: true

{test_job}

build:
  stage: build
  script:
    - {cmds['build']}
  artifacts:
    paths:
      - dist/
      - build/
      - target/
    expire_in: 1 day
  only:
    - {branch}
    - merge_requests

security-scan:
  stage: security
  image: aquasec/trivy:latest
  script:
    - trivy fs --exit-code 0 --severity HIGH,CRITICAL --format json --output trivy-report.json .
    - trivy fs --exit-code 1 --severity CRITICAL . || true
  artifacts:
    when: always
    paths:
      - trivy-report.json
    expire_in: 1 week
  allow_failure: true

{docker_job}

# Workflow rules
workflow:
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "{branch}"'
    - if: '$CI_COMMIT_TAG'
"""
