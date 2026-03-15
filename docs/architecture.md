# System Architecture

The Agentic RAG system is built around the **Model Context Protocol (MCP)**, functioning as an external tool server that gives autonomous AI agents (like Claude Code) semantic search and context retrieval capabilities.

Below are the architectural C4 Model diagrams mapping the relationships of the system.

## Level 1: System Context Diagram

This diagram shows the high-level relationship between the AI Agent, the RAG MCP Server, and external dependencies.

```mermaid
C4Context
    title System Context diagram for Agentic RAG System

    Person(user, "User", "A developer interacting via the terminal or chat interface.")
    
    System_Ext(agent, "AI Agent (Claude Code)", "Local LLM acting as the primary intelligent agent. Executes tools via MCP.")

    System(rag, "RAG MCP Server", "Provides document ingestion, vector retrieval, and direct SQL analytics capabilities to the Agent.")

    System_Ext(ollama, "Ollama (Local)", "Local inference runtime providing dense text embeddings (nomic-embed-text) and metadata extraction (qwen2.5:3b).")

    Rel(user, agent, "Chats with and delegates tasks to", "Text")
    Rel(agent, rag, "Executes tools (ingest, search, sql)", "MCP Protocol (JSON-RPC over stdio)")
    Rel(rag, ollama, "Extracts metadata / Generates embeddings", "HTTP (localhost:11434)")
```

## Level 2: Container Diagram

This diagram dives deeper into the internal containers that make up the RAG MCP Server. We utilize a Python backend for logic and a local Supabase stack for data persistence.

```mermaid
C4Container
    title Container diagram for RAG MCP System

    System_Ext(agent, "AI Agent (Claude Code)", "Client executing MCP tool calls.")
    System_Ext(ollama, "Ollama (Local)", "Local inference runtime. nomic-embed-text for embeddings, qwen2.5:3b for metadata extraction.")

    System_Boundary(rag_system, "RAG MCP Server Stack") {
        Container(mcp_server, "FastMCP Python Server", "Python", "Exposes endpoints, routes inputs, orchestrates NLP models and connections.")

        ContainerDb(supabase_pg, "Supabase Postgres", "PostgreSQL", "Stores document records, vector embeddings, and provides text-to-SQL data via a read-only role.")
        ContainerDb(supabase_storage, "Supabase Storage", "S3 API", "Stores original, unmodified raw document binaries (PDF, HTML, etc).")
    }

    Rel(agent, mcp_server, "Calls MCP Tools via stdio", "stdio")

    Rel(mcp_server, supabase_storage, "Uploads raw files / Deletes raw files", "REST / SDK")
    Rel(mcp_server, supabase_pg, "Queries database (Vector, FTS, Raw SQL) / Stores Chunks", "REST / psycopg2")
    Rel(mcp_server, ollama, "embed_texts() / extract_metadata()", "HTTP (localhost:11434)")

    BiRel(supabase_pg, supabase_storage, "Cascade deletes via foreign keys", "Internal")
```

## Level 3: Component Diagram (FastMCP Server)

This diagram breaks down the internal responsibilities inside the Python `FastMCP` container application.

```mermaid
C4Component
    title Component diagram for FastMCP Python Server

    Container_Boundary(mcp_server, "FastMCP Python Server") {
        Component(tool_ingest, "ingest_file() Tool", "Python", "Handles document uploads, triggers chunking, and maps pipelines.")
        Component(tool_search, "search_documents() Tool", "Python", "Primary interface for Agent knowledge retrieval. Orchestrates vector + FTS.")
        Component(tool_sql, "query_sql() Tool", "Python", "Provides bounded, SELECT-only SQL execution for schema mapping and analytics.")
        
        Component(docling_parser, "Docling Parser", "Python", "Parses complex binary formats (PDF, DOCX, etc) into semantic Markdown.")
        Component(chunker, "Recursive Splitter", "Python", "Splits markdown into character-optimized chunks with overlapping sliding windows.")
        
        Component(hybrid_search, "Hybrid Search Orchestrator", "Python", "Executes cosine similarity (pgvector) and BM25 FTS concurrently.")
        Component(rrf, "RRF Fusion Module", "Python", "Mathematically scores and fuses disparate document hit rankings into a single sorted list.")
        Component(bge_reranker, "Cross-Encoder Reranker", "sentence-transformers", "Executes MS-MARCO MiniLM evaluation over fused snippets for extreme relevancy.")
    }

    Rel(tool_ingest, docling_parser, "Parses incoming files", "Method Call")
    Rel(docling_parser, chunker, "Passes markdown text", "Method Call")
    
    Rel(tool_search, hybrid_search, "Delegates semantic query", "Method Call")
    Rel(hybrid_search, rrf, "Fuses vector and keyword queries", "Method Call")
    Rel(rrf, bge_reranker, "Passes top K fused candidates", "Method Call")
```

## Database Schema Model (Postgres)

This is a simplified entity-relationship visualization of the local Supabase stack.

```mermaid
erDiagram
    DOCUMENTS {
        uuid id PK
        string filename
        string content_hash "SHA256 duplicate constraint"
        string status "pending, completed, failed"
        int chunk_count
        timestamp created_at
        string title "Extracted via LLM schema"
        string summary "Extracted via LLM schema"
        jsonb topics "Array of string concepts"
        string document_type
        string language
    }
    
    CHUNKS {
        uuid id PK
        uuid document_id FK "Cascade Delete on Parent"
        uuid user_id "RLS Ownership"
        int chunk_index
        text content "Actual semantic text"
        vector embedding "768-dim dense representation"
        tsvector fts "Generated standard SQL FTS index"
        timestamp created_at
    }
    
    DOCUMENTS ||--o{ CHUNKS : "Has Many"
```
