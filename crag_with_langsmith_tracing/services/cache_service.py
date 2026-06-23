import hashlib
import json
import logging
from crag_with_langsmith_tracing.clients.redis_client import redis_client
from crag_with_langsmith_tracing.config.settings import settings

logger = logging.getLogger(__name__)

def get_cache_key(query: str) -> str:
    try:
        return hashlib.md5(query.strip().lower().encode()).hexdigest()
    except Exception as e:
        logger.error(f"Error generating cache key: {e}")
        raise e

def get_exact_cache(query: str):
    if not redis_client:
        logger.warning("Redis client is not available")
        return None
    try:
        key = get_cache_key(query)
        value = redis_client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.error(f"Error retrieving exact cache: {e}")
    return None

def save_exact_cache(query: str, data: dict):
    if not redis_client:
        logger.warning("Redis client is not available")
        return
    try:
        key = get_cache_key(query)
        redis_client.setex(
            key,
            settings.EXACT_CACHE_TTL,
            json.dumps(data)
        )
    except Exception as e:
        logger.error(f"Error saving exact cache: {e}")

def get_docs(query: str):
    if not redis_client:
        logger.warning("Redis client is not available")
        return None
    try:
        key = f"docs:{get_cache_key(query)}"
        value = redis_client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.error(f"Error retrieving documents cache: {e}")
    return None

def save_docs(query: str, docs: list):
    if not redis_client:
        logger.warning("Redis client is not available")
        return
    try:
        key = f"docs:{get_cache_key(query)}"
        redis_client.setex(
            key,
            settings.DOCS_CACHE_TTL,
            json.dumps(docs)
        )
    except Exception as e:
        logger.error(f"Error saving documents cache: {e}")
