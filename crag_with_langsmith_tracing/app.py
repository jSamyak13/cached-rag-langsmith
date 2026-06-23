import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from crag_with_langsmith_tracing.api.router import router as api_router
from crag_with_langsmith_tracing.api.schemas import ErrorResponse

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cached RAG API",
    description="Production-grade API for Cached RAG orchestration with LangSmith and MongoDB checkpointer",
    version="1.0.0"
)

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

app.include_router(api_router, prefix="/api")
