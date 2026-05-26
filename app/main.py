"""
Main Application Entrypoint
Agentic Clinical Intelligence Platform

Initializes FastAPI, configures CORS, mounts routers, and defines
the Global Exception Handler linked to the DevSecOps Agent.
"""

import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database.session import init_db, AsyncSessionLocal
from app.agents.devsecops_agent import devsecops_agent
from app.api.middleware.logging_middleware import LoggingMiddleware
from app.api.middleware.rate_limiter import RateLimitMiddleware

# API Routers
from app.api.routes import health
from app.api.routes import analyze
from app.api.routes import chat
from app.api.routes import export

# Configure Logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("healthtech_ai")

# ── Lifespan Manager ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the FastAPI application."""
    logger.info("Starting Agentic Clinical Intelligence Platform...")
    
    # Initialize the database and ensure all tables exist
    await init_db()
    
    yield
    
    logger.info("Shutting down platform services...")


# ── App Initialization ────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Agentic Clinical Intelligence Platform - Hackathon Demo",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# ── Middleware Configuration ──────────────────────────────────────────
# CORS - Allowing all for hackathon environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Middlewares
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)


# ── Global Exception Handler ──────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch all unhandled exceptions, trigger the DevSecOps agent to
    create a GitLab incident, and return a clean 500 response.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])
    logger.error(f"Global unhandled exception [{request_id}]: {exc}")
    
    # Build context for DevSecOps Agent
    error_ctx = devsecops_agent.build_error_context(
        exception=exc,
        request_id=request_id,
        endpoint=request.url.path,
        failed_step="global_exception_handler",
        agent_name="system_monitor"
    )
    
    # Fire off DevSecOps incident logic
    try:
        async with AsyncSessionLocal() as db:
            await devsecops_agent.handle_system_exception(error_context=error_ctx, db=db)
    except Exception as devsecops_exc:
        logger.error(f"DevSecOps Agent failed during exception handling: {devsecops_exc}")
        
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "A critical system error occurred. Our DevSecOps AI has been notified and an incident has been automatically created.",
            "request_id": request_id,
            "disclaimer": settings.disclaimer
        }
    )


# ── Router Registration ───────────────────────────────────────────────
app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(chat.router)
app.include_router(export.router)

@app.get("/")
async def root():
    """Root endpoint verifying API is alive."""
    return {"message": "Agentic Clinical Intelligence Platform API is running.", "version": settings.app_version}
