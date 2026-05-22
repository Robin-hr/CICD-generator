# DevOps Platform

An intelligent DevOps tooling platform — Phase 1 MVP.

## Architecture

```
devops-platform/
├── backend/          # FastAPI (Python)
│   ├── main.py           # API routes
│   ├── repo_scanner.py   # GitHub repo analyzer
│   ├── cicd_generator.py # CI/CD config generator
│   └── requirements.txt
└── frontend/         # React + TypeScript + Vite
    ├── src/
    │   ├── App.tsx
    │   ├── pages/
    │   │   ├── RepoScanner.tsx
    │   │   └── CICDGenerator.tsx
    │   └── utils/api.ts
    └── package.json
```

## Quick Start

### 1. Start the Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Open http://localhost:3000

---

## Phase 1 Features (This Release)

| Feature | Status |
|---------|--------|
| Repo Scanner | ✅ Live |
| CI/CD Generator (GitHub Actions) | ✅ Live |
| CI/CD Generator (Jenkinsfile) | ✅ Live |
| CI/CD Generator (GitLab CI) | ✅ Live |

## Coming in Phase 2

| Feature | Status |
|---------|--------|
| Docker Generator | 🔜 |
| Kubernetes Generator | 🔜 |
| Terraform Generator | 🔜 |
| Security Scanner (Trivy + Checkov) | 🔜 |

## Tech Stack

- **Backend**: FastAPI, httpx, Pydantic
- **Frontend**: React 18, TypeScript, Vite
- **Styling**: Pure CSS (no framework)
- **API**: GitHub REST API v3

## Environment Variables

To avoid GitHub rate limits (60 req/hr unauthenticated):

Backend: No config needed — token is passed per-request from the UI.

For production deployment, set `GITHUB_TOKEN` and use it as a fallback in `repo_scanner.py`.
