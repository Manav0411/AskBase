from typing import List, Dict, Optional
import os
import logging
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

VECTOR_STORE_DIR = "vector_store"
VECTOR_STORE_PATH = os.path.join(VECTOR_STORE_DIR, "faiss_index")

os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

embedding_model = None

cache_metadata = {
    "loaded_at": None,
    "document_count": 0,
    "total_chunks": 0,
    "last_updated": None,
    "search_count": 0,
    "cache_hits": 0
}

def get_embedding_model():
    """Lazy initialization of embedding model - optimized for free tier"""
    from langchain_huggingface import HuggingFaceEmbeddings
    
    global embedding_model
    if embedding_model is None:
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        embedding_model = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={
                'normalize_embeddings': True,
                'batch_size': 16,  # Smaller batches for limited RAM
                'show_progress_bar': False
            }
        )
        logger.info("Embedding model loaded and cached successfully")
    return embedding_model

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
            embeddings = get_embedding_model()
            vector_store = FAISS.load_local(
                VECTOR_STORE_PATH, 
                embeddings,
                allow_dangerous_deserialization=True
            )
            cache_metadata["loaded_at"] = datetime.now()
            cache_metadata["cache_hits"] = 0
            _update_cache_metadata()
            logger.info(f"✓ Vector store loaded and cached from {VECTOR_STORE_PATH}")
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

def ingest_text(document_id: str, text: str):
    """Ingest text into vector store - optimized for free tier"""
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document as LC_Document
    
    global vector_store
    
    logger.info(f"Processing document {document_id}...")
    
    embeddings = get_embedding_model()

    # Use smaller chunks for faster processing on free tier
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len
    )

    chunks = text_splitter.split_text(text)
    logger.info(f"Split document {document_id} into {len(chunks)} chunks")
    
    # Limit chunks to prevent worker timeouts on free tier
    if len(chunks) > 100:
        logger.warning(f"Document has {len(chunks)} chunks, limiting to 100 for free tier")
        chunks = chunks[:100]

    docs = [
        LC_Document(
            page_content=chunk,
            metadata={"document_id": document_id}
        )
        for chunk in chunks
    ]

    # Process in batches to avoid memory issues
    batch_size = 10
    if vector_store is None:
        # Create new vector store with first batch
        first_batch = docs[:batch_size]
        vector_store = FAISS.from_documents(first_batch, embeddings)
        logger.info(f"Created new vector store")
        remaining_docs = docs[batch_size:]
    else:
        remaining_docs = docs
    
    # Add remaining documents in batches
    if remaining_docs:
        total_batches = (len(remaining_docs) + batch_size - 1) // batch_size
        for i in range(0, len(remaining_docs), batch_size):
            batch = remaining_docs[i:i+batch_size]
            vector_store.add_documents(batch)
            batch_num = i // batch_size + 1
            logger.info(f"Processed batch {batch_num}/{total_batches} ({len(batch)} chunks)")
    
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
            embeddings = get_embedding_model()
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
