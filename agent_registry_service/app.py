"""
Agent Registry Service - Main FastAPI Application.

This is the main entry point for the Agent Registry Service API.
It provides endpoints for managing agent registrations and session tracking.

Features:
- Agent Registry management (register, query, update, delete agents)
- Session management (create, track conversations, monitor agent usage)
- Persistent storage with SQLite
- RESTful API with OpenAPI documentation
- Health monitoring and service info
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import time

from agent_registry_service.api import registry_routes, session_routes
from agent_registry_service.registry.agent_registry import AgentRegistry
from agent_registry_service.registry.file_store import FileStore
from agent_registry_service.registry.agent_factory_resolver import AgentFactoryResolver
from agent_registry_service.sessions.session_manager import SessionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
REGISTRY_FILE_PATH = os.getenv("REGISTRY_FILE_PATH", "data/agent_registry.json")
SESSION_DB_PATH = os.getenv("SESSION_DB_PATH", "data/sessions.db")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Global instances (initialized in startup event)
registry_instance: AgentRegistry = None
session_manager_instance: SessionManager = None


# =============================================================================
# Lifespan Event Handler
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown.

    Startup:
    - Initialize AgentRegistry with persistence
    - Initialize SessionManager with SQLite
    - Load registry from file
    - Create database schema

    Shutdown:
    - Close database connections
    - Final registry save
    """
    global registry_instance, session_manager_instance

    # Startup
    logger.info("=" * 60)
    logger.info("Starting Agent Registry Service")
    logger.info("=" * 60)

    try:
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)

        # Initialize FileStore
        logger.info(f"Initializing file store at: {REGISTRY_FILE_PATH}")
        file_store = FileStore(REGISTRY_FILE_PATH)

        # Initialize AgentFactoryResolver
        logger.info("Initializing agent factory resolver")
        factory_resolver = AgentFactoryResolver()

        # Initialize AgentRegistry with persistence
        logger.info("Initializing agent registry")
        registry_instance = AgentRegistry(
            file_store=file_store,
            factory_resolver=factory_resolver,
            auto_load=True  # Load existing agents on startup
        )

        # Inject registry into routes
        registry_routes.set_registry(registry_instance)

        logger.info(f"Loaded {len(registry_instance.agents)} agents from registry")

        # Initialize SessionManager
        logger.info(f"Initializing session manager with database: {SESSION_DB_PATH}")
        session_manager_instance = SessionManager(
            db_path=SESSION_DB_PATH,
            auto_init=True  # Automatically create schema
        )

        # Inject session manager into routes
        session_routes.set_session_manager(session_manager_instance)

        logger.info("Agent Registry Service started successfully")
        logger.info(f"API Documentation available at: http://localhost:8003/docs")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Failed to start Agent Registry Service: {e}", exc_info=True)
        raise

    yield  # Application runs

    # Shutdown
    logger.info("=" * 60)
    logger.info("Shutting down Agent Registry Service")
    logger.info("=" * 60)

    try:
        # Final registry save
        if registry_instance and registry_instance._persistence_enabled():
            logger.info("Saving registry state before shutdown")
            registry_instance._persist()

        logger.info("Shutdown complete")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# =============================================================================
# Create FastAPI Application
# =============================================================================

app = FastAPI(
    title="Agent Registry Service",
    description="""
## Agent Registry Service API

A comprehensive service for managing AI agent registrations and tracking conversation sessions.

### Features

- **Agent Registry**: Register, query, update, and manage AI agents
- **Session Management**: Track user conversations and agent invocations
- **Persistent Storage**: SQLite for sessions, JSON for registry
- **RESTful API**: Full CRUD operations with OpenAPI documentation
- **Production Ready**: Error handling, logging, health monitoring

### API Sections

- **Agent Registry** (`/registry`): Manage agent registrations
- **Session Management** (`/sessions`): Track conversations and agent usage
- **Health** (`/health`): Service health and status monitoring

### Getting Started

1. Check service health: `GET /health`
2. View API docs: Visit `/docs`
3. Create a session: `POST /sessions`
4. Register an agent: `POST /registry/agents`

For detailed information, explore the endpoints below or visit the interactive documentation.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# =============================================================================
# Middleware
# =============================================================================

# CORS Middleware - Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip Middleware - Compress responses
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing information."""
    start_time = time.time()

    # Log request
    logger.info(f"→ {request.method} {request.url.path}")

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log response
    logger.info(
        f"← {request.method} {request.url.path} "
        f"[{response.status_code}] "
        f"({duration:.3f}s)"
    )

    return response


# =============================================================================
# Include Routers
# =============================================================================

app.include_router(
    registry_routes.router,
    tags=["Agent Registry"]
)

app.include_router(
    session_routes.router,
    tags=["Session Management"]
)


# =============================================================================
# Root and Health Endpoints
# =============================================================================

@app.get(
    "/",
    summary="Service Information",
    description="Get information about the Agent Registry Service",
    tags=["Service Info"]
)
async def root() -> Dict[str, Any]:
    """
    Service information endpoint.

    Returns basic information about the service, API version,
    and links to documentation.
    """
    return {
        "service": "Agent Registry Service",
        "version": "1.0.0",
        "status": "running",
        "description": "AI Agent Registration and Session Management Service",
        "documentation": {
            "openapi": "/openapi.json",
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "health": "/health",
            "registry": "/registry",
            "sessions": "/sessions"
        },
        "features": [
            "Agent Registry Management",
            "Session Tracking",
            "Conversation History",
            "Agent Performance Metrics",
            "Persistent Storage"
        ]
    }


@app.get(
    "/health",
    summary="Health Check",
    description="Check service health and database connectivity",
    tags=["Service Info"]
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns the health status of the service including:
    - Service status
    - Database connectivity
    - Registry status
    - Number of registered agents
    - Session manager status
    """
    health = {
        "status": "healthy",
        "service": "Agent Registry Service",
        "version": "1.0.0",
        "components": {}
    }

    # Check Registry
    try:
        if registry_instance:
            agent_count = len(registry_instance.agents)
            health["components"]["registry"] = {
                "status": "healthy",
                "agent_count": agent_count,
                "persistence_enabled": registry_instance._persistence_enabled()
            }
        else:
            health["components"]["registry"] = {
                "status": "not_initialized"
            }
            health["status"] = "degraded"
    except Exception as e:
        health["components"]["registry"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health["status"] = "unhealthy"

    # Check Session Manager
    try:
        if session_manager_instance:
            # Try to get database stats
            from agent_registry_service.sessions.db_init import get_connection, get_database_stats

            conn = get_connection(session_manager_instance.db_path)
            stats = get_database_stats(conn)
            conn.close()

            health["components"]["session_manager"] = {
                "status": "healthy",
                "database": SESSION_DB_PATH,
                "stats": stats
            }
        else:
            health["components"]["session_manager"] = {
                "status": "not_initialized"
            }
            health["status"] = "degraded"
    except Exception as e:
        health["components"]["session_manager"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health["status"] = "unhealthy"

    # Set appropriate status code
    status_code = status.HTTP_200_OK if health["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(content=health, status_code=status_code)


# =============================================================================
# Global Exception Handler
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error": "Internal server error",
            "detail": str(exc) if app.debug else "An unexpected error occurred"
        }
    )


# =============================================================================
# Main Entry Point (for direct execution)
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8003,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
