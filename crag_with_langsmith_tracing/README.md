# cragsmith (Cached RAG with LangSmith Tracing)

A modular, production-ready RAG (Retrieval-Augmented Generation) pipeline built using LangGraph, Redis, and LangChain. It implements a dual-layer caching architecture (cRAG) to reduce API latency and cost, uses LangSmith for runtime tracing, and integrates Ragas for evaluation.

## Key Features

1. **Dual-Layer Redis Caching**:
   - **Document Cache**: Stores retrieved vector store chunks for queries to prevent redundant embedding searches.
   - **Exact Answer Cache**: Stores final assistant answers for identical queries to completely bypass LLM execution.
2. **State Graph Orchestration**: Built with LangGraph using a compiled StateGraph checkpointer to persist conversation history.
3. **Observability**: Seamlessly integrated with LangSmith for logging, profiling, and debugging execution steps.
4. **Evaluation Suite**: Integrated with Ragas to measure Faithfulness, Answer Relevancy, Context Precision, and Context Recall.

## Directory Structure

```
crag_with_langsmith_tracing/
├── main.py
├── config/
│   ├── settings.py
│   └── logging_config.py
├── clients/
│   └── redis_client.py
├── services/
│   ├── cache_service.py
│   └── embeddings_service.py
├── pipeline/
│   └── agent.py
└── evaluation/
    └── evaluator.py
```

## Setup & Installation

### 1. Requirements

Install the necessary dependencies in your virtual environment:

```bash
pip install -r requirements.txt
```

Ensure your `requirements.txt` includes:

```text
langchain
langgraph
langchain_openai
redis
ragas
datasets
pandas
python-dotenv
```

### 2. Environment Variables

Create a `.env` file in the root workspace directory:

```env
OPENAI_API_KEY=your_openai_key
FILE_PATH=data
LLM_MODEL=gpt-4o-mini
EMBEDDINGS_MODEL=text-embedding-3-small
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=crag-with-langsmith
```

### 3. Redis Setup

Start your local Redis instance:

```bash
redis-server
```

To clear the cache at any time, run:

```bash
redis-cli flushdb
```

## Running the Application

### 1. Start the CLI Chat Loop

Run the main application interface:

```bash
python crag_with_langsmith_tracing/main.py
```

### 2. Start the Evaluation Runner

To evaluate the pipeline metrics using Ragas:

```bash
python crag_with_langsmith_tracing/evaluation/evaluator.py
```
