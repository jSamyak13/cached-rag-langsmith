import hashlib
import json
import logging
from crag_with_langsmith_tracing.backend.clients.redis_client import redis_client
from crag_with_langsmith_tracing.backend.config.settings import settings

logger = logging.getLogger(__name__)

def get_cache_key(query: str, user_id: str) -> str:
    try:
        combined = f"{user_id}:{query.strip().lower()}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()
    except Exception as e:
        logger.error(f"Error generating cache key: {e}")
        raise e

def get_exact_cache(query: str, user_id: str):
    if not redis_client:
        logger.warning("Redis client is not available")
        return None
    try:
        key = get_cache_key(query, user_id)
        value = redis_client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.error(f"Error retrieving exact cache: {e}")
    return None

def save_exact_cache(query: str, data: dict, user_id: str):
    if not redis_client:
        logger.warning("Redis client is not available")
        return
    try:
        key = get_cache_key(query, user_id)
        redis_client.setex(
            key,
            settings.EXACT_CACHE_TTL,
            json.dumps(data)
        )
    except Exception as e:
        logger.error(f"Error saving exact cache: {e}")

def get_docs(query: str, user_id: str):
    if not redis_client:
        logger.warning("Redis client is not available")
        return None
    try:
        key = f"docs:{get_cache_key(query, user_id)}"
        value = redis_client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.error(f"Error retrieving documents cache: {e}")
    return None

def save_docs(query: str, docs: list, user_id: str):
    if not redis_client:
        logger.warning("Redis client is not available")
        return
    try:
        key = f"docs:{get_cache_key(query, user_id)}"
        redis_client.setex(
            key,
            settings.DOCS_CACHE_TTL,
            json.dumps(docs)
        )
    except Exception as e:
        logger.error(f"Error saving documents cache: {e}")
