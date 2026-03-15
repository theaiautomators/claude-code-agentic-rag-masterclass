# Sequence Diagrams

These sequence diagrams map the specific operational execution flows of the Agentic RAG system.

## Sequence Diagram: Ingestion Process

This diagram illustrates the flow of data when an AI agent requests to ingest a document into the RAG system.

```mermaid
sequenceDiagram
    actor Agent as AI Agent (MCP Client)
    participant MCP as RAG Server (FastMCP)
    participant Storage as Supabase Storage
    participant DB as Supabase Postgres
    participant Ollama as Ollama (Local)

    Agent->>MCP: ingest_file("doc.pdf")

    activate MCP
    MCP->>MCP: calculate SHA-256 hash
    MCP->>DB: Check if hash exists

    alt Hash exists
        DB-->>MCP: Returns true
        MCP-->>Agent: return "Already ingested"
    else Hash is new
        MCP->>Storage: Upload raw binary file

        MCP->>MCP: parse_document() via Docling
        MCP->>MCP: recursive_split(markdown)

        par Parallel Operations
            MCP->>Ollama: embed_texts(chunks) [nomic-embed-text]
            Ollama-->>MCP: Returns 768-dim Vectors
        and
            MCP->>Ollama: extract_metadata(top 8000 chars) [qwen2.5:3b]
            Ollama-->>MCP: Returns JSON Schema (Title, Tags)
        end

        MCP->>DB: INSERT into documents
        MCP->>DB: INSERT into chunks (content, embedding)
        note right of DB: Postgres calculates `fts` (TSVECTOR)<br/>automatically on insert.

        MCP-->>Agent: return "Ingestion Complete"
    end
    deactivate MCP
```

## Sequence Diagram: Retrieval (Read) Process

This diagram illustrates the dynamic hybrid search + reranking flow when the AI agent queries the system for knowledge.

```mermaid
sequenceDiagram
    actor Agent as AI Agent (MCP Client)
    participant MCP as RAG Server (FastMCP)
    participant Ollama as Ollama (Local)
    participant DB as Supabase Postgres
    participant CrossEncoder as MS-MARCO Reranker

    Agent->>MCP: search_documents(query="foo", mode="hybrid", rerank=true)

    activate MCP

    par Parallel Search Execution
        %% Vector Search Path
        MCP->>Ollama: embed_text("foo") [nomic-embed-text]
        Ollama-->>MCP: Returns 768-dim Vector
        MCP->>DB: rpc("search_chunks", {vector, filters})
        note over DB: Executes Cosine Similarity (pgvector)
        DB-->>MCP: Returns Top K Semantic matches
    and 
        %% Keyword Search Path
        MCP->>DB: rpc("keyword_search_chunks", {query})
        note over DB: Executes BM25 (FTS/ts_rank)
        DB-->>MCP: Returns Top K Exact matches
    end
    
    MCP->>MCP: reciprocal_rank_fusion(vector_hits, keyword_hits)
    note right of MCP: Fuses distinct datasets via RRF formula:<br/>score = sum(1 / (k + rank))
    
    MCP->>CrossEncoder: rerank_results(query, fused_hits)
    note right of CrossEncoder: local sentence-transformers inference
    CrossEncoder-->>MCP: Returns re-scored hits
    
    MCP->>MCP: Sort by reranker_score DESC, limit Top K
    
    MCP-->>Agent: return JSON list of highly relevant Markdown chunks
    deactivate MCP
```
