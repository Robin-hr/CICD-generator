# DevOps Platform - Backend

FastAPI backend for the DevOps Platform.

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Docs

Visit: http://localhost:8000/docs

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/scan/repo` | Scan a GitHub repository |
| POST | `/api/generate/cicd` | Generate CI/CD config |
| GET | `/api/platforms` | List supported CI/CD platforms |

## Example: Scan a Repo

```bash
curl -X POST http://localhost:8000/api/scan/repo \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/tiangolo/fastapi"}'
```

## With GitHub Token (avoids rate limits)

```bash
curl -X POST http://localhost:8000/api/scan/repo \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/owner/repo", "github_token": "ghp_..."}'
```
