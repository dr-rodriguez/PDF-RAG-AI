# Phase 0 Research: RAG Vector Database with Chunking

## Vector Store Selection (ChromaDB vs FAISS vs Others)

- **Decision**: Use ChromaDB for local persistence vector store.
- **Rationale**: 
  - ChromaDB provides excellent local persistence (SQLite-based) suitable for `data/db/` directory storage
  - Native LangChain integration via `langchain-chroma` package
  - Built-in support for metadata filtering (useful for source file tracking and deduplication)
  - Handles incremental additions efficiently (supports append-with-deduplication requirement)
  - Simple directory-based persistence (no separate server process needed)
  - Better suited for metadata queries than FAISS
- **Alternatives considered**:
  - FAISS: High performance but requires manual persistence handling; less convenient for metadata management
  - Qdrant: Requires separate server process; overkill for local-only use case
  - Pinecone/Weaviate: Cloud-based; conflicts with local-only requirement

## LangChain RAG Architecture with Ollama

- **Decision**: Use LangChain's RAG chain pattern with:
  - `langchain.text_splitter.RecursiveCharacterTextSplitter` for chunking (supports overlap)
  - `langchain_community.embeddings.OllamaEmbeddings` for embedding generation
  - `langchain-chroma.Chroma` for vector store
  - `langchain_community.llms.Ollama` for query generation
  - `langchain.chains.RetrievalQA` or `langchain.chains.ConversationalRetrievalChain` for RAG orchestration
- **Rationale**: 
  - Standard LangChain patterns align with official RAG documentation
  - Native Ollama integrations avoid custom API wrappers
  - RetrievalQA chain handles similarity search, filtering, and answer generation
  - Supports configurable retriever with top K and similarity threshold
- **Alternatives considered**:
  - Custom RAG implementation: More control but unnecessary complexity; LangChain provides proven patterns
  - Direct vector store queries without LangChain chains: Possible but loses chain benefits (error handling, prompt templating, etc.)

## Chunking Strategy Implementation

- **Decision**: Use `RecursiveCharacterTextSplitter` with configurable `chunk_size` and `chunk_overlap` parameters loaded from environment variables. Defaults: `chunk_size=1000`, `chunk_overlap=200` (characters).
- **Rationale**:
  - RecursiveCharacterTextSplitter respects text boundaries (paragraphs, sentences) while maintaining approximate size
  - Overlap preserves context across chunk boundaries (important for semantic search)
  - Configurable via env vars satisfies FR-003
  - 1000 character default balances semantic coherence with retrieval granularity
- **Alternatives considered**:
  - Markdown-aware splitters: More complex; fixed-size with overlap meets requirements
  - Sentence transformers chunking: Adds dependency; fixed-size sufficient for initial implementation

## Persistence and Deduplication Strategy

- **Decision**: Store ChromaDB database in `data/db/` directory. Track source file metadata in ChromaDB's metadata store. For deduplication: check if chunk content + source file combination already exists before adding.
- **Rationale**:
  - ChromaDB's metadata filtering enables efficient source file tracking
  - Metadata-based deduplication is simpler than content hashing
  - Directory-based persistence satisfies FR-006 (persistence requirement)
  - ChromaDB handles concurrent access reasonably well (SQLite backend)
- **Alternatives considered**:
  - Content hash-based deduplication: More complex; metadata tracking sufficient
  - Separate deduplication index: Unnecessary overhead; ChromaDB metadata handles this

## Environment Variable Configuration

- **Decision**: Use `python-dotenv` to load `.env` file. Required variables:
  - `OLLAMA_EMBEDDING_MODEL`: Name of Ollama embedding model (e.g., "nomic-embed-text")
  - `OLLAMA_QUERY_MODEL`: Name of Ollama LLM model for querying (e.g., "llama2", "mistral")
  - `CHUNK_SIZE`: Chunk size in characters (default: 1000)
  - `CHUNK_OVERLAP`: Overlap size in characters (default: 200)
  - `RETRIEVER_TOP_K`: Number of top chunks to retrieve (default: 4)
  - `RETRIEVER_MIN_SIMILARITY`: Minimum similarity threshold (default: 0.0, configurable as float)
- **Rationale**: 
  - Standard `.env` format is familiar and easy to configure
  - Sensible defaults enable quick start while allowing customization
  - Missing required variables (embedding/query models) trigger clear errors per FR-008
- **Alternatives considered**:
  - Config file (YAML/TOML): More complex; environment variables sufficient for this scope
  - CLI flags for all parameters: Too verbose; env vars provide persistent configuration

## Retrieval and Answer Generation

- **Decision**: Use LangChain's `RetrievalQA` chain with similarity search retriever. Filter results by minimum similarity threshold before passing to LLM. Output only generated answer text (no source metadata).
- **Rationale**:
  - RetrievalQA handles embedding query, similarity search, and answer generation in one chain
  - Configurable retriever supports top K and similarity filtering
  - Chain abstraction simplifies error handling and logging
  - Answer-only output satisfies FR-011 (no source information)
- **Alternatives considered**:
  - Manual retrieval + separate LLM call: More code; chain abstraction preferred
  - Include source metadata: Conflicts with FR-011 requirement

## Error Handling and Validation

- **Decision**: 
  - Validate Ollama connection and model availability at service initialization
  - Check vector database existence before query operations
  - Provide clear error messages for missing config, unavailable models, empty database
- **Rationale**: 
  - Early validation prevents confusing errors during processing
  - Clear error messages satisfy FR-008
  - Database existence check satisfies FR-007 (empty database handling)
- **Alternatives considered**:
  - Lazy validation: Can lead to confusing mid-process errors; prefer early validation

## Summary of Resolved Clarifications

- **Vector Store**: ChromaDB with local SQLite persistence in `data/db/` directory
- **LangChain Components**: RecursiveCharacterTextSplitter, OllamaEmbeddings, Ollama LLM, Chroma vector store, RetrievalQA chain
- **Chunking**: Fixed-size chunks with overlap using RecursiveCharacterTextSplitter (default: 1000 chars, 200 overlap)
- **Deduplication**: Metadata-based tracking in ChromaDB (source file + content uniqueness check)
- **Configuration**: Environment variables via `.env` file with sensible defaults
- **Retrieval**: Top K chunks above minimum similarity threshold via LangChain retriever
- **Answer Format**: Generated text only (no source metadata)

