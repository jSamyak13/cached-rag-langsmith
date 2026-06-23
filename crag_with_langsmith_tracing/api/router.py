import logging
from fastapi import APIRouter, HTTPException, Depends, status
from crag_with_langsmith_tracing.api.schemas import QueryRequest, QueryResponse, ThreadHistoryResponse, ChatLogItem, ErrorResponse
from crag_with_langsmith_tracing.api.dependencies import verify_rate_limit
from crag_with_langsmith_tracing.pipeline.agent import run_query
from crag_with_langsmith_tracing.clients.mongodb_client import mongo_client
from crag_with_langsmith_tracing.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/query",
    response_model=QueryResponse,
    dependencies=[Depends(verify_rate_limit)],
    responses={
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def query_rag(request: QueryRequest):
    try:
        result = run_query(request.query, request.thread_id)
        return QueryResponse(
            answer=result.get("answer", "An error occurred."),
            sources=result.get("sources", [])
        )
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve answer from cRAG pipeline."
        )

@router.get(
    "/history/{thread_id}",
    response_model=ThreadHistoryResponse,
    responses={
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_thread_history(thread_id: str):
    if not mongo_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB service is not available."
        )
    try:
        db = mongo_client[settings.MONGODB_DB]
        collection = db["chat_history"]
        
        cursor = collection.find({"thread_id": thread_id}).sort("timestamp", 1)
        history = []
        for doc in cursor:
            history.append(
                ChatLogItem(
                    timestamp=doc["timestamp"].isoformat(),
                    user_query=doc["user_query"],
                    ai_response=doc["ai_response"]
                )
            )
        
        return ThreadHistoryResponse(
            thread_id=thread_id,
            history=history
        )
    except Exception as e:
        logger.error(f"Error fetching thread history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve thread history from database."
        )
