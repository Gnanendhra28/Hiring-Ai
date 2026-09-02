import uuid
from contextlib import asynccontextmanager
from typing import Any
from collections.abc import AsyncGenerator
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.api.v1.auth import router as auth_router
from app.api.v1.organizations import router as org_router
from app.api.v1.public_jobs import router as public_jobs_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.job_intelligence import router as job_intel_router
from app.api.v1.matching import router as matching_router
from app.api.v1.scoring import router as scoring_router
from app.api.v1.ranking import router as ranking_router
from app.api.v1.recommendations import router as recommendation_router
from app.api.v1.recruiters import router as recruiters_router
from app.api.v1.resumes import router as resumes_router




from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.candidates import router as candidates_router
from app.api.v1.admin import router as admin_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.interviews import router as interviews_router
from app.api.v1.communications import router as communications_router
from app.api.v1.document_intelligence import router as doc_intel_router
from app.api.v1.requisitions import router as requisitions_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.operations import router as operations_router

import time
from app.core.metrics import metrics
from app.core.rate_limiter import rate_limiter
from app.db.session import engine

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.APP_ENV}]")
    try:
        from app.db.base import Base
        import app.domains.identity.models
        import app.domains.organizations.models
        import app.domains.jobs.models
        import app.domains.candidates.models
        import app.domains.applications.models
        import app.domains.interviews.models
        import app.domains.audit.models
        import app.domains.recommendation.models
        import app.domains.document_intelligence.models
        import app.domains.recruiters.models  # noqa: F401

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            from sqlalchemy import text
            schema_ddl = [
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50);",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN NOT NULL DEFAULT FALSE;",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_platform_admin BOOLEAN NOT NULL DEFAULT FALSE;",
                "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS verification_status VARCHAR(50) NOT NULL DEFAULT 'UNVERIFIED';",
                "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;",
                "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50);",
                "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS resume_url VARCHAR(1024);",
                "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS raw_resume_text TEXT;",
                "ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50);",
                "ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS company_name VARCHAR(255);",
                "ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS website_url VARCHAR(500);",
                "ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS registration_id VARCHAR(255);",
                "ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR(500);",
                "ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS verification_status VARCHAR(50) NOT NULL DEFAULT 'UNVERIFIED';",
                "ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS submitted_at VARCHAR(100);",
            ]
            for ddl in schema_ddl:
                try:
                    await conn.execute(text(ddl))
                except Exception as ex_ddl:
                    logger.warning(f"Schema DDL notice ({ddl}): {ex_ddl}")
        logger.info("Database schema tables and columns verified/created successfully.")
    except Exception as e:
        logger.error(f"Error initializing database tables during startup: {e}")
    yield
    logger.info(f"Graceful shutdown: closing database connection pools for {settings.APP_NAME}")
    try:
        await engine.dispose()
    except Exception as e:
        logger.error(f"Error during database pool shutdown: {e}")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    logger.error(
        f"Unhandled application exception on {request.method} {request.url.path}: {type(exc).__name__}",
        extra={
            "request_id": request_id,
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please try again.",
            "request_id": request_id,
        },
        headers={
            "X-Request-ID": request_id,
            "X-Correlation-ID": correlation_id,
        }
    )

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting Middleware
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next) -> Response:
    is_limited, max_reqs, remaining, reset_ts, retry_after = rate_limiter.is_rate_limited(request)
    if is_limited:
        logger.warning(
            f"[RateLimiter] Rate limit exceeded ({max_reqs} req/min) for path '{request.url.path}'"
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Rate limit exceeded. Too many requests. Please try again shortly.",
                "retry_after_seconds": retry_after,
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(max_reqs),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_ts),
            },
        )
    response: Response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(max_reqs)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_ts)
    return response

# Request Context, Correlation ID & Metrics Middleware
@app.middleware("http")
async def request_context_middleware(request: Request, call_next) -> Response:
    start_t = time.time()
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    request.state.correlation_id = correlation_id
    request.state.request_id = request_id

    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}: {type(exc).__name__}",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
            },
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again.",
                "request_id": request_id,
            },
            headers={
                "X-Request-ID": request_id,
                "X-Correlation-ID": correlation_id,
            }
        )

    duration = time.time() - start_t
    norm_path = metrics.normalize_path(request.url.path)
    metrics.increment(
        "http_requests_total",
        labels={"method": request.method, "path": norm_path, "status": str(response.status_code)}
    )
    metrics.observe_duration(
        "http_request_duration_seconds",
        duration,
        labels={"method": request.method, "path": norm_path}
    )

    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Request-ID"] = request_id
    return response

# Liveness Endpoint
@app.get("/live", tags=["Health"])
@app.get("/api/v1/health/liveness", tags=["Health"])
async def liveness_probe():
    return {
        "status": "alive",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }

# Metrics Endpoint
@app.get("/metrics", tags=["Observability"])
async def get_metrics():
    return Response(content=metrics.export_prometheus(), media_type="text/plain")

# Readiness Endpoint
@app.get("/ready", tags=["Health"])
@app.get("/api/v1/health/readiness", tags=["Health"])
async def readiness_probe():
    checks: dict[str, Any] = {}
    is_ready = True

    if settings.READINESS_CHECK_DB:
        try:
            from app.db.session import check_database_health
            db_healthy = await check_database_health()
            checks["database"] = {"status": "ok" if db_healthy else "error", "provider": "postgresql"}
            if not db_healthy:
                is_ready = False
        except Exception as e:
            logger.error(f"Readiness check failed for database: {e!s}")
            checks["database"] = {"status": "error", "message": str(e)}
            is_ready = False

    # Optional AI Provider Readiness Check (Degraded state does NOT return HTTP 503 if DB is healthy)
    try:
        from app.infrastructure.factories import AIGatewayFactory
        provider = AIGatewayFactory.get_provider()
        checks["ai_provider"] = {
            "status": "ok",
            "provider": provider.__class__.__name__,
        }
    except Exception as e:
        logger.warning(f"AI Provider degraded: {e!s}")
        checks["ai_provider"] = {
            "status": "degraded",
            "message": str(e),
            "note": "Deterministic scoring & ranking remain operational.",
        }

    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if is_ready else "not_ready",
            "environment": settings.APP_ENV,
            "checks": checks,
        }
    )


# Mount API v1 Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(org_router, prefix="/api/v1")
app.include_router(public_jobs_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(job_intel_router, prefix="/api/v1")
app.include_router(matching_router, prefix="/api/v1")
app.include_router(scoring_router, prefix="/api/v1")
app.include_router(ranking_router, prefix="/api/v1")
app.include_router(recommendation_router, prefix="/api/v1")
app.include_router(recruiters_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(candidates_router, prefix="/api/v1")
app.include_router(resumes_router, prefix="/api/v1/resumes", tags=["Candidate Resumes"])
app.include_router(assessments_router, prefix="/api/v1")
app.include_router(interviews_router, prefix="/api/v1")
app.include_router(communications_router, prefix="/api/v1")
app.include_router(doc_intel_router, prefix="/api/v1")
app.include_router(requisitions_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")
app.include_router(operations_router, prefix="/api/v1")

@app.get("/api/v1/health", tags=["Health"])
async def api_health_check():
    return {
        "status": "ok",
        "service": "api_v1",
        "version": settings.APP_VERSION,
    }

@app.get("/api/v1/health/version", tags=["Health"])
async def api_version_check():
    """
    Returns safe application version identification for deployment verification.
    """
    return {
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "commit": "162420e",
        "status": "ACTIVE",
    }

