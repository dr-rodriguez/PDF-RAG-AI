# List of TODOs

## Converter
- [ ] Add ability to skip already converted pages

## RAG
- [ ] Look through DB structure, to understand storage
- [ ] Confirm isolation of vector database collections (eg, DC20 is separate from OSW)
- [ ] Add metadata to the vector database (want to store the source file and page number)
- [ ] Update to use Hybrid Chunking
- [ ] Add ability to query the vector database by metadata (fetch full document by page)
- [ ] Implement Re-ranking (may not be as useful, but could be combined after Self-Reflective strategy)
- [ ] Implement Self-Reflective RAG (score chunks based on relevance, score 1-5, keep > 3)
- [ ] Implement Query Expansion (use LLM to rewrite query with more details)
- [ ] Add option to turn on/off each strategy

## Query
- [ ] Add ability to specify collection to use
- [ ] Add ability to specify model to use

## References
https://github.com/coleam00/ottomator-agents/tree/main/all-rag-strategies
