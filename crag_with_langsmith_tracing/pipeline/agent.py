import logging
import json
from typing import Annotated, List
from typing_extensions import TypedDict
from crag_with_langsmith_tracing.api.schemas import RAGResponse
from langchain.agents import create_agent
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.mongodb import MongoDBSaver
from crag_with_langsmith_tracing.clients.mongodb_client import mongo_client
from crag_with_langsmith_tracing.services.chat_history_service import save_chat_log
from langchain.tools import tool
from langchain_core.messages import AIMessage
from crag_with_langsmith_tracing.config.settings import settings
from crag_with_langsmith_tracing.services.cache_service import get_docs, save_docs, get_exact_cache, save_exact_cache
from crag_with_langsmith_tracing.services.embeddings_service import create_or_load_embeddings
from langchain_openai import ChatOpenAI
from crag_with_langsmith_tracing.prompts.prompt import RAG_PROMPT
from langchain_core.output_parsers import PydanticOutputParser
from tenacity import retry, stop_after_attempt, wait_random_exponential

logger = logging.getLogger(__name__)

@tool
@retry(
    wait=wait_random_exponential(min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True
)
def retrieve_docs(query: str) -> str:
    """
    Queries a vector database containing authoritative knowledge across 6 specific domains:
    1. Large Language Models (LLMs): Comprehensive research overview on architectures, training strategies, and hallucination categories.
    2. TATA IPL 2023 Schedule: Official match dates, times, competing teams (home/away), and venue locations.
    3. Indian Annual Financial Statement (2026-2027): Union budget allocations, receipts, and disbursements across the Consolidated Fund of India and Union Territories.
    4. Chernobyl Nuclear Accident: Scientific context on the 1986 disaster, operator actions, environmental impact, and long-term health statistics.
    5. Indian Income Tax Slabs (FY 2025-26 / AY 2026-27): Complete breakdown of old vs. new tax regimes, exemption limits, rebates, and standard deductions.
    6. MS Dhoni Biography: Complete life profile covering his early years in Ranchi, milestones, and international ICC cricket captaincy records.

    Input must be a fully formed, specific semantic search query.
"""
    try:
        logger.info(f"Retrieve_docs tool called with query: {query}")
        cached_docs = get_docs(query)
        if cached_docs:
            logger.info("Retrieval cache hit")
            if len(cached_docs) > 0:
                logger.info(f"Retrieved 1st document from cache: {cached_docs[0]}")
            return "\n\n".join(cached_docs)
            
        logger.info("Retrieval cache miss, query vectorstore")
        vectordb = create_or_load_embeddings(settings.FILE_PATH)
        if not vectordb:
            logger.error("Vector database is not available for document retrieval")
            return ""
            
        logger.info("Querying vectorstore retriever")
        retriever = vectordb.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5}
        )
        docs = retriever.invoke(query)
        contents = [doc.page_content for doc in docs]
        if len(contents) > 0:
            logger.info(f"Retrieved 1st document from vector store: {contents[0]}")
        save_docs(query, contents)
        return "\n\n".join(contents)
    except Exception as e:
        logger.error(f"Error in retrieve_docs tool: {e}")
        return ""

class State(TypedDict):
    messages: Annotated[list, add_messages]

parser = PydanticOutputParser(pydantic_object=RAGResponse)
SYSTEM_PROMPT = RAG_PROMPT + "\n\n" + parser.get_format_instructions()

try:
    llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0
        )
    rag_agent = create_agent(
        model=llm,
        tools=[retrieve_docs],
        system_prompt=SYSTEM_PROMPT
    )
except Exception as e:
    logger.error(f"Failed to create agent: {e}")
    rag_agent = None

def run_agent(state: State):
    try:
        logger.info(f"Agent node execution started. Input state messages count: {len(state['messages'])}")
        query = state["messages"][-1].content
        logger.info(f"Processing query: {query}")
        
        logger.info("Checking exact cache")
        cached_answer = get_exact_cache(query)
        if cached_answer:
            logger.info(f"Answer cache hit. Cached answer: {cached_answer.get('answer')}")
            return {
                "messages": [
                    AIMessage(
                        content=json.dumps(cached_answer)
                    )
                ]
            }
            
        if not rag_agent:
            raise ValueError("RAG agent is not initialized")
            
        logger.info("Invoking LLM agent")
        result = rag_agent.invoke(state)
        answer = result["messages"][-1].content
        logger.info(f"LLM agent execution finished. Response content: {answer[:15]}")
        
        try:
            parsed = parser.parse(answer)
            answer_dict = parsed.model_dump()
        except Exception as pe:
            logger.warning(f"Failed to parse LLM response as JSON schema: {pe}")
            answer_dict = {"answer": answer, "sources": []}

        logger.info("Saving response to exact cache")
        save_exact_cache(query, answer_dict)
        return {
            "messages": [
                AIMessage(content=json.dumps(answer_dict))
            ]
        }
    except Exception as e:
        logger.error(f"Error in run_agent node: {e}")
        error_dict = {"answer": "An error occurred while processing your request.", "sources": []}
        return {
            "messages": [
                AIMessage(content=json.dumps(error_dict))
            ]
        }

builder = StateGraph(State)
builder.add_node("agent", run_agent)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)

try:
    if mongo_client:
        checkpointer = MongoDBSaver(
            client=mongo_client,
            db_name=settings.MONGODB_DB
        )
        graph = builder.compile(checkpointer=checkpointer)
    else:
        raise ValueError("MongoDB client is not initialized")
except Exception as e:
    logger.error(f"Failed to compile StateGraph: {e}")
    graph = None

def run_query(query: str, thread_id: str) -> dict:
    if not graph:
        logger.error("StateGraph graph is not compiled")
        return {"answer": "System error: StateGraph graph is not compiled", "sources": []}
    try:
        logger.info(f"Starting run_query with thread_id: {thread_id} and query: {query}")
        config = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke({"messages": [("user", query)]}, config=config)
        final_response_str = result["messages"][-1].content
        try:
            final_response = json.loads(final_response_str)
        except Exception:
            final_response = {"answer": final_response_str, "sources": []}
        logger.info(f"run_query completed successfully. Final response: {final_response.get('answer', '')[:10]}")
        save_chat_log(thread_id, query, final_response.get("answer", ""))
        print("="*40, "AI Response Start", "="*40)
        return final_response
    except Exception as e:
        logger.error(f"Error invoking query: {e}")
        return {"answer": "An error occurred during query execution.", "sources": []}


