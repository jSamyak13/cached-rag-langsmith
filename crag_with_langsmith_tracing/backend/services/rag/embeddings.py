import os
import logging
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma
from crag_with_langsmith_tracing.backend.config.settings import settings

logger = logging.getLogger(__name__)
try:
    embeddings_model = OpenAIEmbeddings(
        model=settings.EMBEDDINGS_MODEL,
        openai_api_key=settings.OPENAI_API_KEY
    )
except Exception as e:
    logger.error(f"Failed to initialize embeddings model: {e}")
    embeddings_model = None

def load_data(path: str):
    try:
        logger.info(f"Loading data from PDF: {path}")
        loader = PyPDFLoader(path).load()
        splits = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        ).split_documents(loader)
        return splits
    except Exception as e:
        logger.error(f"Error loading PDF from path {path}: {e}")
        return []

def create_or_load_embeddings(path: str):
    embd_dir = settings.EMBEDDINGS_DIR
    if not embeddings_model:
        logger.error("Embeddings model is not initialized")
        return None
    try:
        if os.path.exists(embd_dir):
            logger.info("Loading existing Chroma vectorstore")
            return Chroma(embedding_function=embeddings_model, persist_directory=embd_dir)
        
        logger.info(f"Creating new Chroma vectorstore from path: {path}")
        text_data = []
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    data = load_data(filepath)
                    text_data.extend(data)
        elif os.path.isfile(path):
            text_data.extend(load_data(path))
        else:
            logger.warning(f"Path {path} does not exist or is not accessible")
            return None
        
        if not text_data:
            logger.warning("No document text was extracted to build embeddings")
            return None
            
        vectorstore = Chroma.from_documents(
            documents=text_data,
            embedding=embeddings_model,
            persist_directory=embd_dir
        )
        logger.info("Chroma vectorstore created and persisted successfully")
        return vectorstore
    except Exception as e:
        logger.error(f"Error in create_or_load_embeddings: {e}")
        return None
