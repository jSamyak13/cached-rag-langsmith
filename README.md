# cragsmith (Cached RAG with LangSmith Tracing & FastAPI)

A modular, production-ready RAG (Retrieval-Augmented Generation) pipeline built using LangGraph, Redis, MongoDB, and LangChain. It implements a dual-layer caching architecture (cRAG) to reduce API latency and cost, uses LangSmith for runtime tracing, persists thread-level execution checkpoints in MongoDB, and exposes a structured FastAPI REST interface with rate limiting and automated backoff retries.

## Key Features

1. **Dual-Layer Redis Caching**:
   * **Document Cache**: Stores retrieved vector store chunks for queries to prevent redundant embedding searches.
   * **Exact Answer Cache**: Stores structured assistant answers for identical queries to completely bypass LLM execution.
2. **MongoDB Checkpoint Persistence**: Implements thread-safe state persistence across sessions using `MongoDBSaver` checkpointer.
3. **Audit Chat Logging**: Stores a human-readable flat history of all user queries and AI responses in a dedicated MongoDB collection (`chat_history`).
4. **FastAPI Web Server**:
   * Decoupled architecture with separate routes, Pydantic validation schemas, and dependency injection.
   * Redis-backed API rate limiting (15 requests per minute per IP).
   * Tenacity-backed exponential backoff retries on downstream document retrieval calls.
5. **Pydantic Output Parsing**: Strict agent-level output validation enforcing that response answers and source citations match predefined JSON structures.
6. **Observability**: Seamlessly integrated with LangSmith for logging, profiling, and debugging execution steps.

## Directory Structure

```text
crag_with_langsmith_tracing/
├── main.py
├── app.py
├── config/
│   ├── settings.py
│   └── logging_config.py
├── clients/
│   ├── redis_client.py
│   └── mongodb_client.py
├── services/
│   ├── auth/
│   │   └── service.py
│   └── rag/
│       ├── cache.py
│       ├── embeddings.py
│       └── chat_history.py
├── pipeline/
│   └── agent.py
└── api/
    ├── auth/
    │   ├── router.py
    │   └── schemas.py
    ├── rag/
    │   ├── router.py
    │   └── schemas.py
    ├── schemas.py
    └── dependencies.py
```

## Setup & Installation

### 1. Installation

Install the necessary dependencies in your virtual environment:

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create or update your `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_key
FILE_PATH=data
LLM_MODEL=gpt-4o-mini
EMBEDDINGS_MODEL=text-embedding-3-small

# Redis Configuration (Caching & Rate Limiting)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
EXACT_CACHE_TTL=3600
DOCS_CACHE_TTL=86400

# MongoDB Configuration (State & Chat Logs)
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=crag_checkpoints

# LangSmith Observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=crag-with-langsmith
```

## Running the Application

### 1. Start the API Server

Run the FastAPI web API:

```bash
uvicorn crag_with_langsmith_tracing.app:app --reload --port 8001
```

Once running, access the interactive Swagger documentation at:
`http://127.0.0.1:8001/docs`

### 2. API Endpoints

#### POST /api/query
Sends a prompt through the RAG pipeline.

* **Request Body**:
  ```json
  {
    "query": "What are the rules of operation?",
    "thread_id": "session_123"
  }
  ```
* **Response**:
  ```json
  {
    "answer": "The foundational rules of operation require reliance on...",
    "sources": [
      "Document excerpt chunk 1...",
      "Document excerpt chunk 2..."
    ]
  }
  ```

#### GET /api/history/{thread_id}
Retrieves human-readable chat logs for a specific conversation session.

* **Response**:
  ```json
  {
    "thread_id": "session_123",
    "history": [
      {
        "timestamp": "2026-06-23T12:00:00Z",
        "user_query": "What are the rules of operation?",
        "ai_response": "The foundational rules..."
      }
    ]
  }
  ```

### 3. Start the CLI Chat Loop

Run the interactive console chat tool:

```bash
python crag_with_langsmith_tracing/main.py
```
