import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from crag_with_langsmith_tracing.backend.config.logging_config import setup_logging
from crag_with_langsmith_tracing.backend.api.rag.router import router as rag_router
from crag_with_langsmith_tracing.backend.api.auth.router import router as auth_router
from crag_with_langsmith_tracing.backend.api.schemas import ErrorResponse

import os
from fastapi.middleware.cors import CORSMiddleware

setup_logging()
logger = logging.getLogger(__name__)

# Load allowed origins from env, including defaults for common React/Vite development ports
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
).split(",")

# Disable Swagger UI docs in production if explicitly configured
docs_url = None if os.getenv("ENV") == "production" else "/docs"
redoc_url = None if os.getenv("ENV") == "production" else "/redoc"

app = FastAPI(
    title="Cached RAG API",
    description="Production-grade API for Cached RAG orchestration with LangSmith and MongoDB checkpointer",
    version="1.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            error_code=f"HTTP_{exc.status_code}"
        ).model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            detail="An internal server error occurred.",
            error_code="INTERNAL_SERVER_ERROR"
        ).model_dump()
    )

app.include_router(rag_router, prefix="/api", tags=["RAG"])
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
