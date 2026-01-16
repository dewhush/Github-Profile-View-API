"""
GitHub Profile View API

A FastAPI-based REST API wrapper for the GitHub Profile Viewer tool.

Created by: dewhush
"""

import os
import logging
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from dotenv import load_dotenv

from viewer import execute_batch_views

# Load environment variables
load_dotenv()

# Configuration
APP_NAME = os.getenv("APP_NAME", "Github-Profile-View-API")
APP_ENV = os.getenv("APP_ENV", "development")
API_KEY = os.getenv("API_KEY", "")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ASCII Art Banner
BANNER = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     ██████╗ ██╗████████╗██╗  ██╗██╗   ██╗██████╗          ║
║    ██╔════╝ ██║╚══██╔══╝██║  ██║██║   ██║██╔══██╗         ║
║    ██║  ███╗██║   ██║   ███████║██║   ██║██████╔╝         ║
║    ██║   ██║██║   ██║   ██╔══██║██║   ██║██╔══██╗         ║
║    ╚██████╔╝██║   ██║   ██║  ██║╚██████╔╝██████╔╝         ║
║     ╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝          ║
║                                                           ║
║              PROFILE VIEW API                             ║
║                                                           ║
║              Created by: dewhush                          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(BANNER)
    logger.info(f"Starting {APP_NAME} in {APP_ENV} mode")
    logger.info("API is ready to receive requests")
    yield
    # Shutdown
    logger.info("Shutting down API...")


# FastAPI app
app = FastAPI(
    title=APP_NAME,
    description="REST API for GitHub Profile Viewer - Simulate profile views on GitHub",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# ============== MODELS ==============

class ViewRequest(BaseModel):
    """Request model for profile view endpoint."""
    username: str = Field(..., description="Target GitHub username", min_length=1)
    view_count: int = Field(..., description="Number of views to generate", ge=1, le=100)
    max_workers: Optional[int] = Field(5, description="Max concurrent threads", ge=1, le=20)


class ViewResponse(BaseModel):
    """Response model for profile view endpoint."""
    username: str
    total_count: int
    success_count: int
    failed_count: int
    status: str
    message: str


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str


class StatusResponse(BaseModel):
    """Response model for status endpoint."""
    app_name: str
    environment: str
    version: str
    status: str
    timestamp: str


# ============== AUTHENTICATION ==============

async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """Verify API key from header."""
    if not API_KEY:
        # If no API key configured, allow all requests (development mode)
        return True
    
    if x_api_key is None or x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    return True


# ============== ROUTES ==============

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint.
    
    Returns the current health status of the API.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/status", response_model=StatusResponse, tags=["System"])
async def get_status():
    """
    Get API status information.
    
    Returns detailed information about the API status and configuration.
    """
    return StatusResponse(
        app_name=APP_NAME,
        environment=APP_ENV,
        version="1.0.0",
        status="running",
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/v1/view", response_model=ViewResponse, tags=["Profile View"])
async def execute_view(
    request: ViewRequest,
    _: bool = Depends(verify_api_key)
):
    """
    Execute profile views on a GitHub profile.
    
    This endpoint simulates multiple visits to a GitHub profile using
    headless Chrome browsers with anti-detection features.
    
    **Requires API Key authentication via X-API-Key header.**
    
    - **username**: Target GitHub username
    - **view_count**: Number of views to generate (1-100)
    - **max_workers**: Maximum concurrent threads (1-20, default: 5)
    """
    try:
        logger.info(f"Starting view job: @{request.username} x{request.view_count}")
        
        result = execute_batch_views(
            username=request.username,
            view_count=request.view_count,
            max_workers=request.max_workers or 5
        )
        
        return ViewResponse(
            username=result.username,
            total_count=result.total_count,
            success_count=result.success_count,
            failed_count=result.failed_count,
            status=result.status,
            message=f"Completed {result.success_count}/{result.total_count} views successfully"
        )
        
    except Exception as e:
        logger.error(f"Error executing views: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error executing views: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# ============== MAIN ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=APP_ENV == "development"
    )
