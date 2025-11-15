"""
Dividend API - Main Application

Production-grade FastAPI application for dividend investors.
Provides comprehensive access to stock prices, dividend data, ETF holdings, and analytics.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import JSONResponse, FileResponse
import time
import logging
from typing import Dict, Any

# Import routers
from api.routers import stocks, dividends, screeners, etfs, analytics, search, api_keys, auth, bulk
# Note: Rate limiting is now handled by tier_enforcer middleware, not separate rate limiters
from api.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Dividend API",
    description="Production-grade API for dividend investors",
    version="1.0.0",
    docs_url=None,  # Disabled - use custom docs at port 3000
    redoc_url=None,  # Disabled - use custom docs at port 3000
    openapi_url=None,  # Disabled - use custom docs at port 3000
    # Stripe-like branding
    openapi_tags=[
        {
            "name": "stocks",
            "description": "Stock and ETF information with dividend data"
        },
        {
            "name": "dividends",
            "description": "Historical and future dividend payments"
        },
        {
            "name": "screeners",
            "description": "Pre-built stock screeners for dividend investors"
        },
        {
            "name": "etfs",
            "description": "ETF holdings and classification"
        },
        {
            "name": "prices",
            "description": "Historical and real-time price data"
        },
        {
            "name": "analytics",
            "description": "Portfolio analytics and dividend projections"
        },
        {
            "name": "search",
            "description": "Search stocks by symbol, name, or sector"
        },
        {
            "name": "api_keys",
            "description": "API key management and authentication"
        }
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Configure from environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
)

# Session middleware (required for OAuth)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="session",
    max_age=1800,  # 30 minutes
    same_site="lax",
    https_only=False  # Set to True in production with HTTPS
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Note: Rate limiting is now handled by tier_enforcer middleware via database,
# not the standalone RateLimiterMiddleware. Per-minute and monthly limits are
# enforced in individual routers using the enforce_rate_limit dependency.

# Request timing and rate limiting middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time header and enforce rate limiting."""
    start_time = time.time()

    # Skip rate limiting for health check and root endpoints
    if request.url.path in ["/health", "/"]:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.3f}s"
        return response

    # Rate limiting is handled in individual routers with dependencies
    # This middleware just adds timing headers
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.3f}s"
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions with proper error format."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "api_error",
                "message": "An internal server error occurred",
                "code": "internal_error"
            }
        }
    )


# Health check endpoint
@app.get("/health", tags=["system"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring.

    Returns API status and database connectivity.
    """
    try:
        from supabase_helpers import get_supabase_client

        # Test database connection
        supabase = get_supabase_client()
        result = supabase.table('raw_stocks').select('symbol', count='exact').limit(1).execute()

        return {
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "version": "1.0.0",
                "database": "disconnected",
                "error": str(e),
                "timestamp": time.time()
            }
        )


# Root endpoint
@app.get("/", tags=["system"])
async def root() -> Dict[str, Any]:
    """
    API root endpoint.

    Provides API information and links to documentation.
    """
    return {
        "name": "Dividend API",
        "version": "1.0.0",
        "description": "Production-grade API for dividend investors",
        "documentation": settings.FRONTEND_URL,
        "base_url": "/v1",
        "status": "operational",
        "endpoints": {
            "stocks": "/v1/stocks",
            "dividends": "/v1/dividends",
            "screeners": "/v1/screeners",
            "etfs": "/v1/etfs",
            "prices": "/v1/prices",
            "analytics": "/v1/analytics",
            "search": "/v1/search"
        }
    }


# Include auth router (no /v1 prefix for OAuth callbacks)
app.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include routers with /v1 prefix
app.include_router(stocks.router, prefix="/v1", tags=["stocks"])
app.include_router(dividends.router, prefix="/v1", tags=["dividends"])
app.include_router(screeners.router, prefix="/v1", tags=["screeners"])
app.include_router(etfs.router, prefix="/v1", tags=["etfs"])
app.include_router(analytics.router, prefix="/v1", tags=["analytics"])
app.include_router(search.router, prefix="/v1", tags=["search"])
app.include_router(api_keys.router, prefix="/v1", tags=["api_keys"])
app.include_router(bulk.router, prefix="/v1", tags=["bulk"])


# Serve static HTML pages for login and dashboard
@app.get("/login", include_in_schema=False)
async def serve_login():
    """Serve the login page."""
    return FileResponse("web/login.html")


@app.get("/dashboard", include_in_schema=False)
async def serve_dashboard():
    """Serve the dashboard page."""
    return FileResponse("web/dashboard.html")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    logger.info("Dividend API starting up...")
    logger.info("Version: 1.0.0")
    logger.info("Environment: production")

    # Test database connection
    try:
        from supabase_helpers import get_supabase_client
        supabase = get_supabase_client()
        result = supabase.table('raw_stocks').select('symbol', count='exact').limit(1).execute()
        logger.info(f"Database connected: {result.count:,} symbols available")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    logger.info("Dividend API shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
