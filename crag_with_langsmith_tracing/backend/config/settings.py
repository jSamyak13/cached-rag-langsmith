import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    FILE_PATH = os.getenv("FILE_PATH", "data")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB = os.getenv("MONGODB_DB", "crag_checkpoints")
    EMBEDDINGS_DIR = os.getenv("EMBEDDINGS_DIR", "Embeddings")
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))
    EXACT_CACHE_TTL = int(os.getenv("EXACT_CACHE_TTL", 86400))
    DOCS_CACHE_TTL = int(os.getenv("DOCS_CACHE_TTL", 21600))
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

settings = Settings()

if not settings.JWT_SECRET_KEY or not settings.JWT_REFRESH_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY and JWT_REFRESH_SECRET_KEY must be set in the environment. "
        "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )
if len(settings.JWT_SECRET_KEY) < 32 or len(settings.JWT_REFRESH_SECRET_KEY) < 32:
    raise RuntimeError("JWT secrets must be at least 32 characters long.")



