import logging
from typing import Annotated
from typing_extensions import TypedDict
from langchain.agents import create_agent
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import tool
from langchain_core.messages import AIMessage
from config.settings import settings
from services.cache_service import get_docs, save_docs, get_exact_cache, save_exact_cache
from services.embeddings_service import create_or_load_embeddings
from langchain_openai import ChatOpenAI
from prompts.prompt import RAG_PROMPT

logger = logging.getLogger(__name__)

@tool
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

try:
    llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0
        )
    rag_agent = create_agent(
        model=llm,
        tools=[retrieve_docs],
        system_prompt=RAG_PROMPT
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
            logger.info(f"Answer cache hit. Cached answer: {cached_answer['answer']}")
            return {
                "messages": [
                    AIMessage(
                        content=cached_answer["answer"]
                    )
                ]
            }
            
        if not rag_agent:
            raise ValueError("RAG agent is not initialized")
            
        logger.info("Invoking LLM agent")
        result = rag_agent.invoke(state)
        answer = result["messages"][-1].content
        logger.info(f"LLM agent execution finished. Response answer: {answer[:15]}")
        
        logger.info("Saving response to exact cache")
        save_exact_cache(query, answer)
        return {
            "messages": [
                result["messages"][-1]
            ]
        }
    except Exception as e:
        logger.error(f"Error in run_agent node: {e}")
        return {
            "messages": [
                AIMessage(content="An error occurred while processing your request.")
            ]
        }

builder = StateGraph(State)
builder.add_node("agent", run_agent)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)

try:
    graph = builder.compile(checkpointer=InMemorySaver())
except Exception as e:
    logger.error(f"Failed to compile StateGraph: {e}")
    graph = None

def run_query(query: str, thread_id: str) -> str:
    if not graph:
        logger.error("StateGraph graph is not compiled")
        return "System error: StateGraph graph is not compiled"
    try:
        logger.info(f"Starting run_query with thread_id: {thread_id} and query: {query}")
        config = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke({"messages": [("user", query)]}, config=config)
        final_response = result["messages"][-1].content
        logger.info(f"run_query completed successfully. Final response: {final_response[:10]}")
        print("="*40, "AI Response Start", "="*40)
        return final_response
    except Exception as e:
        logger.error(f"Error invoking query: {e}")
        return "An error occurred during query execution."


