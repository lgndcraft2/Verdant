from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.auth import verify_api_key, verify_supabase_jwt
from api.config import get_settings
from api.routers.audit import router as audit_router
from api.routers.keys import router as keys_router
from api.routers.pipeline import router as pipeline_router
from api.routers.providers import router as providers_router
from api.routers.reports import router as reports_router
from api.routers.webhooks import router as webhooks_router
from api.services.cache_service import CacheService
from api.services.claude_service import ClaudeService
from api.services.db_service import DBService
from api.services.gemini_service import GeminiService
from sdk.verdant.pipeline import VerdantPipeline

logger = logging.getLogger(__name__)


def _envelope(data: Any = None, meta: dict[str, Any] | None = None, error: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"data": data, "meta": meta or {}, "error": error}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    cache = CacheService(settings)
    db = DBService(settings)
    claude = ClaudeService(settings, db_service=db)
    gemini = GeminiService(settings, db_service=db)
    pipeline = VerdantPipeline(
        settings,
        claude_service=claude,
        gemini_service=gemini,
        cache_service=cache,
        db_service=db,
    )

    app.state.settings = settings
    app.state.cache = cache
    app.state.db = db
    app.state.claude = claude
    app.state.gemini = gemini
    app.state.pipeline = pipeline

    try:
        await cache.ping()
        await db.ping()
    except Exception as exc:
        logger.warning("VERDANT backend warmup encountered a non-fatal issue: %s", exc)

    yield

    try:
        await cache.close()
    except Exception as exc:
        logger.warning("Cache shutdown failed: %s", exc)
    try:
        await db.close()
    except Exception as exc:
        logger.warning("DB shutdown failed: %s", exc)


app = FastAPI(
    title="VERDANT API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(error={"message": exc.detail, "type": "http_error"}),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_envelope(error={"message": "Request validation failed", "details": exc.errors()}),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled VERDANT API error: %s", exc)
    return JSONResponse(
        status_code=500,
        content=_envelope(error={"message": "Internal server error", "type": exc.__class__.__name__}),
    )


# SDK / programmatic surface — authenticated with a VERDANT API key.
app.include_router(pipeline_router, dependencies=[Depends(verify_api_key)])
app.include_router(audit_router, dependencies=[Depends(verify_api_key)])
app.include_router(webhooks_router, dependencies=[Depends(verify_api_key)])
app.include_router(reports_router, dependencies=[Depends(verify_api_key)])

# Dashboard management surface — authenticated with the user's Supabase session.
app.include_router(keys_router)
app.include_router(providers_router, dependencies=[Depends(verify_supabase_jwt)])
