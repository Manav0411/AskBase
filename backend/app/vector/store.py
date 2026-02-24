from typing import List, Dict, Optional
import os
import logging
import numpy as np
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

VECTOR_STORE_DIR = "vector_store"
VECTOR_STORE_PATH = os.path.join(VECTOR_STORE_DIR, "faiss_index")

os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

cohere_client = None
cohere_embeddings_wrapper = None

cache_metadata = {
    "loaded_at": None,
    "document_count": 0,
    "total_chunks": 0,
    "last_updated": None,
    "search_count": 0,
    "cache_hits": 0
}

def get_cohere_client():
    """Lazy initialization of Cohere client"""
    import cohere
    
    global cohere_client
    if cohere_client is None:
        if not settings.cohere_api_key:
            raise ValueError("COHERE_API_KEY environment variable not set")
        logger.info("Initializing Cohere client")
        cohere_client = cohere.Client(settings.cohere_api_key)
        logger.info("Cohere client initialized successfully")
    return cohere_client

def generate_cohere_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using Cohere API (free tier: 100 calls/min)"""
    client = get_cohere_client()
    
    # Cohere supports up to 96 texts per request
    batch_size = 96
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        logger.info(f"Generating embeddings for batch {i//batch_size + 1} ({len(batch)} texts)")
        
        response = client.embed(
            texts=batch,
            model="embed-english-light-v3.0",  # Free tier model
            input_type="search_document"  # For document indexing
        )
        
        all_embeddings.extend(response.embeddings)
    
    return all_embeddings

def get_cohere_embeddings():
    """Get Cohere embeddings wrapper (cached)"""
    from langchain_core.embeddings import Embeddings
    
    global cohere_embeddings_wrapper
    
    if cohere_embeddings_wrapper is None:
        class CohereEmbeddingsWrapper(Embeddings):
            """Wrapper to make Cohere embeddings compatible with LangChain"""
            
            def embed_documents(self, texts: List[str]) -> List[List[float]]:
                return generate_cohere_embeddings(texts)
            
            def embed_query(self, text: str) -> List[float]:
                client = get_cohere_client()
                response = client.embed(
                    texts=[text],
                    model="embed-english-light-v3.0",
                    input_type="search_query"
                )
                return response.embeddings[0]
        
        cohere_embeddings_wrapper = CohereEmbeddingsWrapper()
        logger.info("Cohere embeddings wrapper initialized")
    
    return cohere_embeddings_wrapper

vector_store = None

def _update_cache_metadata():
    """Update cache metadata after loading or modifying vector store"""
    global cache_metadata, vector_store
    
    if vector_store is not None:
        try:
            total_chunks = len(vector_store.index_to_docstore_id)
            
            unique_docs = set()
            for doc_id in vector_store.index_to_docstore_id.values():
                doc = vector_store.docstore.search(doc_id)
                if doc and "document_id" in doc.metadata:
                    unique_docs.add(doc.metadata["document_id"])
            
            cache_metadata["total_chunks"] = total_chunks
            cache_metadata["document_count"] = len(unique_docs)
            cache_metadata["last_updated"] = datetime.now()
            
            logger.info(f"Cache updated: {len(unique_docs)} documents, {total_chunks} chunks")
        except Exception as e:
            logger.error(f"Failed to update cache metadata: {str(e)}")

def load_vector_store():
    """Load FAISS vector store from disk if it exists (with caching)"""
    from langchain_community.vectorstores import FAISS
    
    global vector_store, cache_metadata
    
    if os.path.exists(VECTOR_STORE_PATH):
        try:
            embeddings = get_cohere_embeddings()
            
            vector_store = FAISS.load_local(
                VECTOR_STORE_PATH, 
                embeddings,
                allow_dangerous_deserialization=True
            )
            cache_metadata["loaded_at"] = datetime.now()
            cache_metadata["cache_hits"] = 0
            _update_cache_metadata()
            logger.info(f"✓ Vector store loaded from {VECTOR_STORE_PATH}")
        except Exception as e:
            logger.error(f"Failed to load vector store: {str(e)}")
            vector_store = None
            cache_metadata["loaded_at"] = None

def save_vector_store():
    """Save FAISS vector store to disk"""
    global vector_store
    
    if vector_store is not None:
        try:
            vector_store.save_local(VECTOR_STORE_PATH)
            logger.info(f"Vector store saved to {VECTOR_STORE_PATH}")
        except Exception as e:
            logger.error(f"Failed to save vector store: {str(e)}")

def simple_text_splitter(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Simple text splitter without ML dependencies - optimized for free tier.
    Splits text into chunks with specified size and overlap.
    """
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        
        # If this isn't the last chunk, try to break at a sentence or word boundary
        if end < text_length:
            # Look for sentence boundaries (. ! ?) within the last 100 chars
            chunk_text = text[start:end]
            last_period = max(
                chunk_text.rfind('. '),
                chunk_text.rfind('! '),
                chunk_text.rfind('? ')
            )
            
            if last_period > chunk_size * 0.5:  # Only break if it's not too early
                end = start + last_period + 1
            else:
                # Try to break at a space instead
                chunk_text = text[start:end]
                last_space = chunk_text.rfind(' ')
                if last_space > chunk_size * 0.7:
                    end = start + last_space
        
        chunks.append(text[start:end].strip())
        start = end - chunk_overlap if end < text_length else end
    
    return chunks

def ingest_text(document_id: str, text: str):
    """Ingest text into vector store using Cohere API"""
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document as LC_Document
    
    global vector_store
    
    logger.info(f"Processing document {document_id} with Cohere API")
    
    embeddings = get_cohere_embeddings()

    # Use simple text splitter (no ML dependencies)
    chunks = simple_text_splitter(
        text, 
        chunk_size=settings.chunk_size, 
        chunk_overlap=settings.chunk_overlap
    )
    logger.info(f"Split document {document_id} into {len(chunks)} chunks")
    
    # Limit chunks to prevent excessive API calls (Cohere free tier: 100 calls/min)
    # With Cohere's batch size of 96, we can process 100 chunks in ~2 API calls
    if len(chunks) > 100:
        logger.warning(f"Document has {len(chunks)} chunks, limiting to 100")
        chunks = chunks[:100]

    docs = [
        LC_Document(
            page_content=chunk,
            metadata={"document_id": document_id}
        )
        for chunk in chunks
    ]

    # With Cohere, we can process all documents at once (up to 96 per API call)
    # The embeddings wrapper handles batching automatically
    if vector_store is None:
        # Create new vector store
        vector_store = FAISS.from_documents(docs, embeddings)
        logger.info(f"Created new vector store with {len(docs)} chunks")
    else:
        # Add documents to existing vector store
        vector_store.add_documents(docs)
        logger.info(f"Added {len(docs)} chunks to existing vector store")
    
    logger.info(f"Document {document_id} fully processed: {len(chunks)} total chunks")
    save_vector_store()
    _update_cache_metadata()

def retrieve(query: str, document_id: str = None, k: int = 4, use_mmr: bool = None):
    """
    Retrieve relevant documents using similarity search or MMR (cached).
    
    Args:
        query: Search query
        document_id: Optional document ID to filter results
        k: Number of documents to return
        use_mmr: Use MMR for diversity (default: from settings)
    
    Returns:
        List of relevant documents
    """
    global vector_store, cache_metadata

    cache_metadata["search_count"] += 1

    if vector_store is None:
        load_vector_store()
    
    if vector_store is None:
        logger.warning("No vector store available for search")
        return []

    cache_metadata["cache_hits"] += 1

    if use_mmr is None:
        use_mmr = settings.use_mmr
    
    if use_mmr:
        results = vector_store.max_marginal_relevance_search(
            query,
            k=k,
            fetch_k=settings.mmr_fetch_k,
            lambda_mult=1.0 - settings.mmr_diversity
        )
        logger.debug(f"Retrieved {len(results)} documents using MMR (diversity={settings.mmr_diversity})")
    else:
        results = vector_store.similarity_search(query, k=k)
        logger.debug(f"Retrieved {len(results)} documents using similarity search")

    if document_id:
        results = [
            doc for doc in results
            if doc.metadata.get("document_id") == document_id
        ]

    return results


def delete_document_vectors(document_id: str):
    """
    Delete all vectors associated with a document.
    Note: FAISS doesn't support deletion by metadata, so we rebuild the index without the document.
    """
    from langchain_community.vectorstores import FAISS
    
    global vector_store
    
    if vector_store is None:
        load_vector_store()
    
    if vector_store is None:
        logger.warning(f"No vector store to delete from for document {document_id}")
        return
    
    try:
        docstore = vector_store.docstore
        index_to_docstore_id = vector_store.index_to_docstore_id
        
        docs_to_keep = []
        for idx, doc_id in index_to_docstore_id.items():
            doc = docstore.search(doc_id)
            if doc and doc.metadata.get("document_id") != document_id:
                docs_to_keep.append(doc)
        
        if docs_to_keep:
            embeddings = get_cohere_embeddings()
            vector_store = FAISS.from_documents(docs_to_keep, embeddings)
            save_vector_store()
            _update_cache_metadata()
            logger.info(f"Rebuilt vector store after deleting document {document_id}. Kept {len(docs_to_keep)} chunks.")
        else:
            vector_store = None
            if os.path.exists(VECTOR_STORE_PATH):
                import shutil
                shutil.rmtree(VECTOR_STORE_DIR)
                os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
            cache_metadata["total_chunks"] = 0
            cache_metadata["document_count"] = 0
            cache_metadata["last_updated"] = datetime.now()
            logger.info(f"Vector store cleared after deleting last document {document_id}")
    
    except Exception as e:
        logger.error(f"Error deleting vectors for document {document_id}: {str(e)}")
        raise


def retrieve_first_chunks(document_id: str, k: int = 6):
    """
    Retrieve the first K chunks of a document in order.
    Useful for summary requests when semantic search isn't appropriate.
    
    Args:
        document_id: Document ID to retrieve chunks from
        k: Number of chunks to return (default: 6)
    
    Returns:
        List of first K document chunks
    """
    global vector_store
    
    if vector_store is None:
        load_vector_store()
    
    if vector_store is None:
        return []
    
    try:
        docstore = vector_store.docstore
        index_to_docstore_id = vector_store.index_to_docstore_id
        
        doc_chunks = []
        for idx, doc_id in sorted(index_to_docstore_id.items()):  # Sort by index for chronological order
            doc = docstore.search(doc_id)
            if doc and doc.metadata.get("document_id") == document_id:
                doc_chunks.append(doc)
        
        result = doc_chunks[:k]
        logger.debug(f"Retrieved first {len(result)} chunks for document {document_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving first chunks for document {document_id}: {str(e)}")
        return []


def get_cache_stats() -> Dict[str, any]:
    """
    Get current cache statistics and metadata.
    
    Returns:
        Dictionary with cache information including:
        - loaded_at: When cache was last loaded
        - document_count: Number of unique documents
        - total_chunks: Total number of text chunks
        - search_count: Total searches performed
        - cache_hits: Number of times cache was used
        - cache_hit_rate: Percentage of searches using cached data
        - last_updated: When cache was last modified
        - is_loaded: Whether vector store is currently loaded
    """
    global cache_metadata, vector_store
    
    hit_rate = 0.0
    if cache_metadata["search_count"] > 0:
        hit_rate = (cache_metadata["cache_hits"] / cache_metadata["search_count"]) * 100
    
    return {
        "is_loaded": vector_store is not None,
        "loaded_at": cache_metadata["loaded_at"].isoformat() if cache_metadata["loaded_at"] else None,
        "document_count": cache_metadata["document_count"],
        "total_chunks": cache_metadata["total_chunks"],
        "search_count": cache_metadata["search_count"],
        "cache_hits": cache_metadata["cache_hits"],
        "cache_hit_rate": round(hit_rate, 2),
        "last_updated": cache_metadata["last_updated"].isoformat() if cache_metadata["last_updated"] else None,
    }


def reload_cache():
    """
    Force reload the vector store from disk.
    Useful for refreshing cache after external changes.
    """
    global vector_store
    vector_store = None
    load_vector_store()
    logger.info("Cache manually reloaded")
