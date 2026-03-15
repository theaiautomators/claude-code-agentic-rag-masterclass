---
description: Interact with the Agentic RAG Masterclass MCP Server
argument-hint: [action] [arguments...]
---

# RAG Database Operations

Execute: `$ARGUMENTS`

This command provides direct instructions for interacting with the `rag-masterclass` MCP server. 

## Process

1. **Identify the Intent**: Read `$ARGUMENTS` to determine which MCP tool is required for the user's request.
   
2. **Select the Correct Tool**:
   - For **ingesting or uploading documents**: Use `mcp_rag-masterclass_ingest_file(file_path)`
   - For **searching the vector database**: Use `mcp_rag-masterclass_search_documents(query, [top_k, threshold, document_type, topics])`
   - For **listing available files**: Use `mcp_rag-masterclass_list_documents()`
   - For **deleting files from the database**: Use `mcp_rag-masterclass_delete_document(document_id)`
   - For **testing basic connection health**: Use `mcp_rag-masterclass_hello(name)` or `mcp_rag-masterclass_supabase_health()`

3. **Execute and Report**:
   - Run the relevant MCP tool, parsing the JSON responses.
   - If searching, present the summary, title, and most relevant chunks back to the user in a readable markdown format.
   - If ingesting, confirm the total number of chunks created and any parsed metadata (like `document_type` and `topics`).
