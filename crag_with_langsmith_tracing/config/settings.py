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

settings = Settings()
