import logging
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, status, Query
from crag_with_langsmith_tracing.backend.api.schemas import ErrorResponse
from crag_with_langsmith_tracing.backend.api.rag.schemas import (
    QueryRequest, QueryResponse, ThreadHistoryResponse, ChatLogItem,
    CreateThreadResponse, ThreadListResponse, ThreadItem
)
from crag_with_langsmith_tracing.backend.api.dependencies import verify_rate_limit, get_current_user
from crag_with_langsmith_tracing.backend.pipeline.agent import run_query
from crag_with_langsmith_tracing.backend.clients.mongodb_client import mongo_client
from crag_with_langsmith_tracing.backend.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/chat/thread",
    response_model=CreateThreadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def create_chat_thread(
    title: str = Query("New Chat", description="Optional title for the chat thread"),
    current_user: dict = Depends(get_current_user)
):
    if not mongo_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB service is not available."
        )
    user_id = current_user["sub"]
    thread_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)
    
    try:
        db = mongo_client[settings.MONGODB_DB]
        collection = db["chat_threads"]
        
        thread_doc = {
            "thread_id": thread_id,
            "user_id": user_id,
            "title": title,
            "created_at": created_at
        }
        collection.insert_one(thread_doc)
        
        return CreateThreadResponse(
            thread_id=thread_id,
            user_id=user_id,
            title=title,
            created_at=created_at.isoformat()
        )
    except Exception as e:
        logger.error(f"Error creating chat thread: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create a new chat session."
        )

@router.get(
    "/chat/threads",
    response_model=ThreadListResponse,
    responses={
        401: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def list_chat_threads(current_user: dict = Depends(get_current_user)):
    if not mongo_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB service is not available."
        )
    user_id = current_user["sub"]
    try:
        db = mongo_client[settings.MONGODB_DB]
        collection = db["chat_threads"]
        
        cursor = collection.find({"user_id": user_id}).sort("created_at", -1)
        threads = []
        for doc in cursor:
            threads.append(
                ThreadItem(
                    thread_id=doc["thread_id"],
                    user_id=user_id,
                    title=doc["title"],
                    created_at=doc["created_at"].isoformat()
                )
            )
        return ThreadListResponse(threads=threads)
    except Exception as e:
        logger.error(f"Error listing chat threads: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat sessions list."
        )

@router.delete(
    "/chat/thread/{thread_id}",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def delete_chat_thread(thread_id: str, current_user: dict = Depends(get_current_user)):
    if not mongo_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB service is not available."
        )
    user_id = current_user["sub"]
    try:
        db = mongo_client[settings.MONGODB_DB]
        threads_col = db["chat_threads"]
        history_col = db["chat_history"]
        
        thread = threads_col.find_one({"thread_id": thread_id})
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found."
            )
        if thread["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat session."
            )
            
        threads_col.delete_one({"thread_id": thread_id})
        history_col.delete_many({"thread_id": thread_id, "user_id": user_id})
        
        return {"message": "Chat session and all related history logs deleted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat thread {thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chat session."
        )

@router.post(
    "/query",
    response_model=QueryResponse,
    dependencies=[Depends(verify_rate_limit)],
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def query_rag(request: QueryRequest, current_user: dict = Depends(get_current_user)):
    if not mongo_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB service is not available."
        )
    user_id = current_user["sub"]
    
    if request.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. The provided user_id does not match the authenticated session."
        )
        
    try:
        db = mongo_client[settings.MONGODB_DB]
        threads_col = db["chat_threads"]
        
        thread = threads_col.find_one({"thread_id": request.thread_id})
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat thread session not found. Please create a thread session first."
            )
        if thread["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat thread session."
            )
            
        result = run_query(request.query, request.thread_id, user_id)
        return QueryResponse(
            answer=result.get("answer", "An error occurred."),
            sources=result.get("sources", [])
        )
    except HTTPException:
        raise
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
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_thread_history(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of history records to return"),
    offset: int = Query(0, ge=0, description="Number of history records to skip")
):
    if not mongo_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB service is not available."
        )
    user_id = current_user["sub"]
    try:
        db = mongo_client[settings.MONGODB_DB]
        threads_col = db["chat_threads"]
        
        thread = threads_col.find_one({"thread_id": thread_id})
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat thread session not found."
            )
        if thread["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat thread session."
            )
            
        history_col = db["chat_history"]
        cursor = history_col.find(
            {"thread_id": thread_id, "user_id": user_id}
        ).sort("timestamp", 1).skip(offset).limit(limit)
        
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
            user_id=user_id,
            history=history
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching thread history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve thread history from database."
        )
