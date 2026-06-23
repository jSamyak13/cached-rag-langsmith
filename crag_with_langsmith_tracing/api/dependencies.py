import logging
from fastapi import HTTPException, status, Request
from crag_with_langsmith_tracing.clients.redis_client import redis_client

logger = logging.getLogger(__name__)

def verify_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not redis_client:
        return
    try:
        key = f"rate_limit:{client_ip}"
        current = redis_client.get(key)
        if current and int(current) >= 15:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        pipeline = redis_client.pipeline()
        pipeline.incr(key)
        pipeline.expire(key, 60)
        pipeline.execute()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking rate limit in Redis: {e}")
