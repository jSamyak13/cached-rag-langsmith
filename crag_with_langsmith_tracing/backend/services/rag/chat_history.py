import logging
from datetime import datetime, timezone
from crag_with_langsmith_tracing.backend.clients.mongodb_client import mongo_client
from crag_with_langsmith_tracing.backend.config.settings import settings

logger = logging.getLogger(__name__)

def save_chat_log(thread_id: str, user_query: str, ai_response: str, user_id: str):
    if not mongo_client:
        logger.warning("MongoDB client is not available, chat log not saved")
        return
    try:
        db = mongo_client[settings.MONGODB_DB]
        collection = db["chat_history"]
        log_entry = {
            "thread_id": thread_id,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc),
            "user_query": user_query,
            "ai_response": ai_response
        }
        collection.insert_one(log_entry)
        logger.info(f"Chat log successfully persisted to MongoDB for thread: {thread_id}")
    except Exception as e:
        logger.error(f"Error saving chat log to MongoDB: {e}")
