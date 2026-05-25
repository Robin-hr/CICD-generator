from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx
import base64
import json
import re
import os
from dotenv import load_dotenv
from repo_scanner import RepoScanner
from cicd_generator import CICDGenerator
from ai_generator import AIGenerator

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="DevOps Platform API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RepoScanRequest(BaseModel):
    repo_url: str
    github_token: Optional[str] = None
    ai_config: Optional[dict] = {}

class CICDGenerateRequest(BaseModel):
    repo_info: dict
    platform: str  # github_actions | jenkins | gitlab_ci
    options: Optional[dict] = {}
    use_ai: Optional[bool] = False
    ai_config: Optional[dict] = {}  # { api_key, model, provider }
    target_cloud: Optional[str] = "AWS"
    deployment_strategy: Optional[str] = "Serverless"

@app.get("/")
async def root():
    return {"message": "DevOps Platform API", "version": "1.0.0", "status": "operational"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/scan/repo")
async def scan_repo(request: RepoScanRequest):
    # Use provided token or fallback to environment variable
    github_token = request.github_token or os.getenv("GITHUB_TOKEN")
    scanner = RepoScanner(github_token=github_token)
    try:
        result = await scanner.scan(request.repo_url)
        
        # AI Config with environmental fallbacks
        ai_config = request.ai_config or {}
        if ai_config.get("api_key") or os.getenv("AI_API_KEY"):
            try:
                generator = AIGenerator(
                    api_key=ai_config.get("api_key") or os.getenv("AI_API_KEY"),
                    model=ai_config.get("model") or os.getenv("AI_MODEL", "gpt-3.5-turbo"),
                    base_url=ai_config.get("base_url") or os.getenv("AI_BASE_URL")
                )
                descriptions = await generator.analyze_structure(result["file_tree_sample"])
                result["structure_descriptions"] = descriptions
            except Exception as e:
                print(f"Structure analysis failed: {e}")
                result["structure_descriptions"] = {}
        else:
            result["structure_descriptions"] = {}
        
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@app.post("/api/generate/cicd")
async def generate_cicd(request: CICDGenerateRequest):
    try:
        if request.use_ai:
            # AI Config with environmental fallbacks
            ai_config = request.ai_config or {}
            api_key = ai_config.get("api_key") or os.getenv("AI_API_KEY")
            model = ai_config.get("model") or os.getenv("AI_MODEL", "gpt-3.5-turbo")
            base_url = ai_config.get("base_url") or os.getenv("AI_BASE_URL")
            
            if not api_key:
                raise ValueError("API key is required for AI generation (provide it in request or set AI_API_KEY environment variable).")
                
            generator = AIGenerator(
                api_key=api_key,
                model=model,
                base_url=base_url
            )
            result = await generator.generate(
                repo_info=request.repo_info,
                platform=request.platform,
                file_contents=request.repo_info.get("file_contents", {}),
                target_cloud=request.target_cloud,
                deployment_strategy=request.deployment_strategy,
                hierarchical_tree=request.repo_info.get("file_tree_hierarchical"),
                structure_descriptions=request.repo_info.get("structure_descriptions")
            )
        else:
            generator = CICDGenerator()
            result = generator.generate(
                repo_info=request.repo_info,
                platform=request.platform,
                options=request.options
            )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

class PipeLineChatRequest(BaseModel):
    pipeline_code: str
    user_message: str
    repo_info: dict
    platform: str
    ai_config: Optional[dict] = {}

@app.post("/api/chat/pipeline")
async def chat_pipeline(request: PipeLineChatRequest):
    try:
        # AI Config with environmental fallbacks
        ai_config = request.ai_config or {}
        api_key = ai_config.get("api_key") or os.getenv("AI_API_KEY")
        
        if not api_key:
            raise ValueError("AI API key is required for chat (provide it in request or set AI_API_KEY environment variable).")
            
        generator = AIGenerator(
            api_key=api_key,
            model=ai_config.get("model") or os.getenv("AI_MODEL", "gpt-3.5-turbo"),
            base_url=ai_config.get("base_url") or os.getenv("AI_BASE_URL")
        )
        response = await generator.chat(
            pipeline_code=request.pipeline_code,
            user_message=request.user_message,
            repo_info=request.repo_info,
            platform=request.platform
        )
        return {"success": True, "data": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.get("/api/platforms")
async def get_platforms():
    return {
        "platforms": [
            {"id": "github_actions", "name": "GitHub Actions", "icon": "github", "description": "Native GitHub CI/CD"},
            {"id": "jenkins", "name": "Jenkinsfile", "icon": "jenkins", "description": "Jenkins Pipeline"},
            {"id": "gitlab_ci", "name": "GitLab CI", "icon": "gitlab", "description": "GitLab CI/CD"},
        ]
    }
