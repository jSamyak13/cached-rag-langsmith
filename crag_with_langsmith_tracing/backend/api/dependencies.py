import logging
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from crag_with_langsmith_tracing.backend.clients.redis_client import redis_client
from crag_with_langsmith_tracing.backend.services.auth.service import verify_access_token

logger = logging.getLogger(__name__)

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    payload = verify_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

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

def verify_auth_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not redis_client:
        return
    try:
        key = f"auth_rate_limit:{client_ip}"
        current = redis_client.get(key)
        if current and int(current) >= 10:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many authentication requests. Please try again later."
            )
        pipeline = redis_client.pipeline()
        pipeline.incr(key)
        pipeline.expire(key, 60)
        pipeline.execute()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking auth rate limit: {e}")

