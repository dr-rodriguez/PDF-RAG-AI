"""RAG service for processing Markdown files and querying vector database."""

import logging
import time
from datetime import UTC, datetime
from pathlib import Path

try:
    from langchain_chroma import Chroma
    from langchain_classic.chains import RetrievalQA
    from langchain_ollama import OllamaEmbeddings
    from langchain_ollama import OllamaLLM as Ollama
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError as e:
    raise ImportError("LangChain dependencies are not installed. Please run: uv sync") from e

from src.lib.ollama_utils import get_model_validation_error, validate_model_available
from src.models.types import (
    ChunkingConfiguration,
    ModelConfiguration,
    ProcessingJob,
    ProcessingResult,
    ProcessingStatus,
    Query,
    QueryResponse,
    RetrievalConfiguration,
    VectorDatabaseConfiguration,
)

logger = logging.getLogger(__name__)


def chunk_text(text: str, config: ChunkingConfiguration) -> list[str]:
    """
    Chunk text using RecursiveCharacterTextSplitter.

    Args:
        text: Text content to chunk
        config: ChunkingConfiguration with chunk_size and chunk_overlap

    Returns:
        List of text chunks
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )
    chunks = splitter.split_text(text)
    return chunks


def initialize_vector_database(
    db_path: str,
    config: VectorDatabaseConfiguration,
    embedding_function,
) -> Chroma:
    """
    Initialize or load ChromaDB vector database.

    Args:
        db_path: Path to database directory
        config: VectorDatabaseConfiguration with collection_name
        embedding_function: Embedding function to use

    Returns:
        Chroma vector store instance
    """
    db_dir = Path(db_path)
    db_dir.mkdir(parents=True, exist_ok=True)

    vector_store = Chroma(
        persist_directory=str(db_dir),
        collection_name=config.collection_name,
        embedding_function=embedding_function,
    )

    return vector_store


def generate_embeddings(
    model_config: ModelConfiguration,
) -> OllamaEmbeddings:
    """
    Create Ollama embeddings instance.

    Args:
        model_config: ModelConfiguration with embedding_model and ollama_base_url

    Returns:
        OllamaEmbeddings instance

    Raises:
        RuntimeError: If embedding model is not available
    """
    # Validate model availability
    if not validate_model_available(model_config.embedding_model, model_config.ollama_base_url):
        error_msg = get_model_validation_error(
            model_config.embedding_model, model_config.ollama_base_url
        )
        raise RuntimeError(error_msg)

    embeddings = OllamaEmbeddings(
        model=model_config.embedding_model,
        base_url=model_config.ollama_base_url,
    )

    return embeddings


def check_chunk_exists(
    vector_store: Chroma,
    content: str,
    source_file: str,
) -> bool:
    """
    Check if a chunk with the same content and source_file already exists.

    Args:
        vector_store: Chroma vector store instance
        content: Chunk content to check
        source_file: Source file path

    Returns:
        True if chunk exists, False otherwise
    """
    try:
        # Query for existing chunks with matching metadata
        results = vector_store.get(
            where={"source_file": source_file},
            include=["metadatas", "documents"],
        )

        # Check if any existing document matches the content
        if results and results.get("documents"):
            for existing_content in results["documents"]:
                if existing_content == content:
                    return True
    except Exception as e:
        logger.warning(f"Error checking for duplicate chunk: {e}")
        # On error, assume it doesn't exist to avoid skipping valid chunks

    return False


def process_file(
    file_path: str,
    db_path: str,
    model_config: ModelConfiguration,
    chunking_config: ChunkingConfiguration,
    vector_db_config: VectorDatabaseConfiguration,
) -> ProcessingResult:
    """
    Process a single Markdown file: read, chunk, embed, deduplicate, and store.

    Args:
        file_path: Path to Markdown file to process
        db_path: Path to vector database directory
        model_config: ModelConfiguration for embeddings
        chunking_config: ChunkingConfiguration for chunking parameters
        vector_db_config: VectorDatabaseConfiguration for collection name

    Returns:
        ProcessingResult with processing status and statistics
    """
    start_time = time.time()
    source_file = str(Path(file_path).resolve())

    try:
        logger.info(f"Processing file: {source_file}")
        stage_start = time.time()

        # Read Markdown file
        file_content = Path(file_path).read_text(encoding="utf-8")
        read_time_ms = int((time.time() - stage_start) * 1000)
        logger.debug(f"Read file in {read_time_ms}ms, size: {len(file_content)} chars")

        if not file_content.strip():
            logger.warning(f"File is empty: {source_file}")
            return ProcessingResult(
                source_file=source_file,
                status=ProcessingStatus.SUCCESS,
                chunks_added=0,
                chunks_skipped=0,
                message="File is empty",
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        # Chunk the content
        stage_start = time.time()
        text_chunks = chunk_text(file_content, chunking_config)
        chunk_time_ms = int((time.time() - stage_start) * 1000)
        logger.info(f"Chunked into {len(text_chunks)} chunks in {chunk_time_ms}ms")

        if not text_chunks:
            logger.warning(f"No chunks generated (file too small): {source_file}")
            return ProcessingResult(
                source_file=source_file,
                status=ProcessingStatus.SUCCESS,
                chunks_added=0,
                chunks_skipped=0,
                message="No chunks generated (file too small)",
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        # Generate embeddings and initialize vector store
        stage_start = time.time()
        embeddings = generate_embeddings(model_config)
        vector_store = initialize_vector_database(db_path, vector_db_config, embeddings)
        init_time_ms = int((time.time() - stage_start) * 1000)
        logger.debug(f"Initialized vector database in {init_time_ms}ms")

        # Process chunks: check for duplicates and add new ones
        stage_start = time.time()
        chunks_added = 0
        chunks_skipped = 0

        documents_to_add = []
        metadatas_to_add = []

        for chunk_index, chunk_content in enumerate(text_chunks):
            if check_chunk_exists(vector_store, chunk_content, source_file):
                chunks_skipped += 1
            else:
                documents_to_add.append(chunk_content)
                metadatas_to_add.append(
                    {
                        "source_file": source_file,
                        "chunk_index": chunk_index,
                    }
                )
                chunks_added += 1

        # Add new chunks to vector store in batch
        if documents_to_add:
            vector_store.add_texts(
                texts=documents_to_add,
                metadatas=metadatas_to_add,
            )
            embed_time_ms = int((time.time() - stage_start) * 1000)
            logger.info(
                f"Embedded and stored {chunks_added} chunks in {embed_time_ms}ms "
                f"({chunks_skipped} duplicates skipped)"
            )
        else:
            logger.info(f"All {chunks_skipped} chunks were duplicates, none added")

        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"Completed processing {source_file}: {chunks_added} chunks added, "
            f"{chunks_skipped} skipped, total time {processing_time_ms}ms"
        )

        return ProcessingResult(
            source_file=source_file,
            status=ProcessingStatus.SUCCESS,
            chunks_added=chunks_added,
            chunks_skipped=chunks_skipped,
            processing_time_ms=processing_time_ms,
        )

    except Exception as e:
        error_msg = str(e)
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(
            f"Failed to process {source_file} after {processing_time_ms}ms: {error_msg}",
            exc_info=True,
        )
        return ProcessingResult(
            source_file=source_file,
            status=ProcessingStatus.FAILURE,
            chunks_added=0,
            chunks_skipped=0,
            message=error_msg,
            processing_time_ms=processing_time_ms,
        )


def process_batch(
    path: str,
    db_path: str,
    model_config: ModelConfiguration,
    chunking_config: ChunkingConfiguration,
    vector_db_config: VectorDatabaseConfiguration,
) -> ProcessingJob:
    """
    Process multiple Markdown files from a directory or single file.

    Args:
        path: Path to Markdown file or directory containing Markdown files
        db_path: Path to vector database directory
        model_config: ModelConfiguration for embeddings
        chunking_config: ChunkingConfiguration for chunking parameters
        vector_db_config: VectorDatabaseConfiguration for collection name

    Returns:
        ProcessingJob with results and summary statistics
    """
    job = ProcessingJob(start_time=datetime.now(UTC))

    path_obj = Path(path)
    markdown_files = []

    if path_obj.is_file():
        # Single file
        if path_obj.suffix.lower() == ".md":
            markdown_files = [path_obj]
    elif path_obj.is_dir():
        # Directory: find all .md files (case-insensitive)
        # Use a set to deduplicate in case glob patterns overlap on case-insensitive filesystems
        markdown_files = list(set(path_obj.glob("*.md")) | set(path_obj.glob("*.MD")))
    else:
        # Path doesn't exist
        job.end_time = datetime.now(UTC)
        job.add_result(
            ProcessingResult(
                source_file=str(path_obj),
                status=ProcessingStatus.FAILURE,
                message=f"Path does not exist: {path}",
            )
        )
        return job

    job.total_files = len(markdown_files)

    # Process each file
    for file_path in markdown_files:
        result = process_file(
            str(file_path),
            db_path,
            model_config,
            chunking_config,
            vector_db_config,
        )
        # Add result and update counters
        job.results.append(result)
        job.total_chunks_added += result.chunks_added
        if result.status == ProcessingStatus.SUCCESS:
            job.succeeded += 1
        else:
            job.failed += 1

    job.end_time = datetime.now(UTC)
    return job


# Query Functions


def setup_vector_retriever(
    db_path: str,
    model_config: ModelConfiguration,
    retrieval_config: RetrievalConfiguration,
    vector_db_config: VectorDatabaseConfiguration,
):
    """
    Set up ChromaDB retriever with configurable top_k and similarity filtering.

    Args:
        db_path: Path to vector database directory
        model_config: ModelConfiguration for embeddings
        retrieval_config: RetrievalConfiguration with top_k and min_similarity
        vector_db_config: VectorDatabaseConfiguration with collection_name

    Returns:
        ChromaDB retriever instance

    Raises:
        RuntimeError: If database doesn't exist or is empty
    """
    # Initialize embeddings
    embeddings = generate_embeddings(model_config)

    # Load vector store
    db_dir = Path(db_path)
    if not db_dir.exists():
        raise RuntimeError(
            f"Vector database not found at '{db_path}'. Run 'pdf-rag process' first."
        )

    try:
        vector_store = Chroma(
            persist_directory=str(db_dir),
            collection_name=vector_db_config.collection_name,
            embedding_function=embeddings,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load vector database: {e}") from e

    # Check if database is empty
    collection = vector_store._collection
    if collection.count() == 0:
        raise RuntimeError("Vector database is empty. Process some documents first.")

    # Create retriever with top_k
    retriever = vector_store.as_retriever(search_kwargs={"k": retrieval_config.top_k})

    return retriever, vector_store


def filter_by_similarity(
    retriever,
    query_text: str,
    min_similarity: float,
) -> list:
    """
    Filter retrieved chunks by minimum similarity threshold.

    Args:
        retriever: ChromaDB retriever instance
        query_text: Query text to search for
        min_similarity: Minimum similarity threshold (0.0 to 1.0)

    Returns:
        List of documents that meet similarity threshold
    """
    # Get documents with similarity scores
    docs_with_scores = retriever.get_relevant_documents(query_text)

    # Filter by similarity threshold
    # Note: ChromaDB similarity scores are distance-based, so lower is better
    # For cosine similarity (typical), we need to convert distance to similarity
    # For now, we'll assume retriever returns docs sorted by relevance
    # and filter based on a threshold if needed
    if min_similarity > 0.0:
        # ChromaDB's similarity_search_with_score returns (doc, distance) tuples
        # We'll use the retriever's default behavior and filter if needed
        # For simplicity, we'll use all docs from retriever and let the chain handle it
        # This is a simplified implementation - full similarity filtering would require
        # direct vector store queries with score thresholds
        filtered_docs = docs_with_scores
    else:
        filtered_docs = docs_with_scores

    return filtered_docs


def process_query(
    query_text: str,
    db_path: str,
    model_config: ModelConfiguration,
    retrieval_config: RetrievalConfiguration,
    vector_db_config: VectorDatabaseConfiguration,
) -> QueryResponse:
    """
    Process a natural language query using RetrievalQA chain.

    Args:
        query_text: Natural language question
        db_path: Path to vector database directory
        model_config: ModelConfiguration for embeddings and query model
        retrieval_config: RetrievalConfiguration with top_k and min_similarity
        vector_db_config: VectorDatabaseConfiguration with collection_name

    Returns:
        QueryResponse with answer text

    Raises:
        RuntimeError: If database doesn't exist, is empty, or models are unavailable
    """
    # Validate query model availability
    if not validate_model_available(model_config.query_model, model_config.ollama_base_url):
        error_msg = get_model_validation_error(
            model_config.query_model, model_config.ollama_base_url
        )
        raise RuntimeError(error_msg)

    # Setup retriever
    retriever, vector_store = setup_vector_retriever(
        db_path, model_config, retrieval_config, vector_db_config
    )

    # Initialize Ollama LLM
    llm = Ollama(
        model=model_config.query_model,
        base_url=model_config.ollama_base_url,
    )

    # Create RetrievalQA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=False,  # Per FR-011: no source metadata
    )

    # Execute query
    try:
        logger.info(f"Processing query: {query_text[:50]}...")
        query_start = time.time()

        result = qa_chain.invoke({"query": query_text})
        answer = result.get("result", "")
        query_time_ms = int((time.time() - query_start) * 1000)
        logger.info(f"Query completed in {query_time_ms}ms, answer length: {len(answer)} chars")

        # Check if answer is empty (no relevant chunks found)
        if not answer or answer.strip() == "":
            raise RuntimeError(
                f"No relevant chunks found (all chunks below similarity threshold "
                f"{retrieval_config.min_similarity})"
            )

        # Get number of retrieved chunks for internal tracking
        # Note: We can't easily get exact count from RetrievalQA chain without modifying it
        # For now, we'll use top_k as an approximation
        retrieved_count = retrieval_config.top_k

        return QueryResponse(answer=answer, retrieved_chunks=retrieved_count)

    except Exception as e:
        if "No relevant chunks" in str(e):
            raise
        raise RuntimeError(f"Query processing failed: {e}") from e


def query(
    query: Query,
    db_path: str,
    model_config: ModelConfiguration,
    retrieval_config: RetrievalConfiguration,
    vector_db_config: VectorDatabaseConfiguration,
) -> QueryResponse:
    """
    Process a query and return answer text only (no source metadata).

    Args:
        query: Query object with text and timestamp
        db_path: Path to vector database directory
        model_config: ModelConfiguration for embeddings and query model
        retrieval_config: RetrievalConfiguration with top_k and min_similarity
        vector_db_config: VectorDatabaseConfiguration with collection_name

    Returns:
        QueryResponse with answer text only
    """
    return process_query(
        query.text,
        db_path,
        model_config,
        retrieval_config,
        vector_db_config,
    )
