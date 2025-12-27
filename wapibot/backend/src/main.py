"""FastAPI application entry point.

Modern async lifespan management for DSPy configuration.
"""

import asyncio
import logging
import hashlib
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.dspy_config import dspy_configurator
from core.warmup import warmup_service
from core.checkpointer import checkpointer_manager
from db.connection import db_connection
from api.router_registry import register_all_routes

# Security imports
from core.security_config import security_settings
from security.secret_manager import secret_manager
from middlewares.auth.auth_middleware import AuthMiddleware
from middlewares.auth.jwt_validator import JWTValidator
from middlewares.auth.api_key_validator import APIKeyValidator
from middlewares.rate_limit.rate_limit_middleware import RateLimitMiddleware

# Setup logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic.

    Modern FastAPI 0.115+ lifespan handler.
    """
    # Startup
    logger.info("🚀 Starting WapiBot Backend V2...")

    # Initialize database tables
    try:
        await db_connection.init_tables()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

    # Configure DSPy with selected LLM provider
    try:
        dspy_configurator.configure()
        logger.info(f"✅ DSPy configured with {settings.primary_llm_provider}")
    except Exception as e:
        logger.error(f"❌ DSPy configuration failed: {e}")
        raise

    # Initialize LangGraph checkpointers (in-memory + SQLite backup)
    try:
        await checkpointer_manager.initialize()
        logger.info("✅ Checkpointers initialized")
    except Exception as e:
        logger.error(f"❌ Checkpointer initialization failed: {e}")
        raise

    # Start LLM warmup (non-blocking)
    asyncio.create_task(warmup_service.startup_warmup())

    # Start idle monitor in background (uses config for all parameters)
    asyncio.create_task(warmup_service.start_idle_monitor())

    yield

    # Shutdown
    logger.info("🛑 Shutting down WapiBot Backend V2...")

    # Cleanup checkpointers
    await checkpointer_manager.shutdown()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers (only in production)."""
    response = await call_next(request)
    if security_settings.is_production:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Server"] = "WapiBot"
    return response

# Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)

# Authentication Middleware
try:
    # Decrypt API keys
    admin_key = secret_manager.decrypt_value(security_settings.api_key_admin or "")
    brain_key = secret_manager.decrypt_value(security_settings.api_key_brain or "")

    # Initialize validators
    validators = [
        JWTValidator(secret_key=security_settings.jwt_secret_key or "dev_secret"),
        APIKeyValidator(valid_keys={
            hashlib.sha256(admin_key.encode()).hexdigest(): {
                "name": "admin_key",
                "scopes": ["admin", "payments", "brain"]
            },
            hashlib.sha256(brain_key.encode()).hexdigest(): {
                "name": "brain_key",
                "scopes": ["brain"]
            }
        } if admin_key and brain_key else {})
    ]

    app.add_middleware(AuthMiddleware, validators=validators)
    logger.info(f"🔐 Security initialized (mode: {security_settings.environment})")
except Exception as e:
    logger.warning(f"⚠️  Security initialization skipped: {e}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only methods we actually use
    allow_headers=["Content-Type", "Accept", "Authorization", "X-API-Key"],  # Added X-API-Key
)


# Activity tracking middleware
@app.middleware("http")
async def track_activity(request: Request, call_next):
    """Track API activity for idle warmup monitoring."""
    # Update activity timestamp on each request
    warmup_service.update_activity()
    response = await call_next(request)
    return response


# Register all API routers (centralized in router_registry.py)
register_all_routes(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
