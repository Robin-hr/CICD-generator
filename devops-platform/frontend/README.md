# DevOps Platform - Frontend

React + TypeScript frontend for the DevOps Platform.

## Setup

```bash
cd frontend
npm install
```

## Run (Development)

```bash
npm run dev
# Open http://localhost:3000
```

## Build (Production)

```bash
npm run build
npm run preview
```

## Requirements

- Node.js 18+
- Backend running at http://localhost:8000

## Features

### Repo Scanner
- Paste any GitHub URL and scan instantly
- Detects: primary language, all languages with % breakdown
- Detects: framework (React, FastAPI, Spring Boot, etc.)
- Detects: package manager (npm, pip, Poetry, Maven, etc.)
- Detects: deployment style (Docker, GitHub Actions, K8s, etc.)
- Detects: test framework
- Shows CI/CD, Dockerfile, test presence indicators

### CI/CD Generator
- Select from GitHub Actions, Jenkinsfile, or GitLab CI
- Generated config is tailored to your exact stack
- Includes install, lint, test, build, security scan stages
- Docker build & push when Dockerfile is present
- Copy to clipboard or download file
- Syntax-highlighted code viewer
