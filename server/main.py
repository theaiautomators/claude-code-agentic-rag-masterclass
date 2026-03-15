import os
import hashlib
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from supabase import create_client

from server.chunking import recursive_split, markdown_split
from server.embeddings import embed_texts, embed_text, embed_chunks_with_context
from server.metadata import extract_metadata
from server.parser import parse_document
from server.search import reciprocal_rank_fusion
from server.reranker import rerank_results

load_dotenv()

mcp = FastMCP("rag-masterclass")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def _get_supabase():
    """Get a Supabase client instance."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


@mcp.tool()
def hello(name: str = "world") -> str:
    """Say hello — verifies the MCP server is working."""
    return f"Hello, {name}! RAG Masterclass MCP server is running."


@mcp.tool()
def supabase_health() -> dict:
    """Check Supabase local stack connectivity."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return {"status": "error", "message": "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env"}

    try:
        client = _get_supabase()
        users = client.auth.admin.list_users()
        return {
            "status": "connected",
            "supabase_url": SUPABASE_URL,
            "auth_users_count": len(users) if users else 0,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def ingest_file(
    file_path: str,
    force: bool = False,
    project: str | None = None,
    create_project: bool = False,
) -> dict:
    """Ingest a file: read → chunk → embed → store in pgvector.

    Skips ingestion if content is unchanged (same hash). If the same filename
    exists with a different hash, the old document is deleted and re-ingested.
    Use force=True to re-ingest even when the hash matches.

    When a project is identified (via explicit `project` arg or LLM extraction),
    the document is linked to that project. If the project doesn't exist yet,
    set create_project=True to create it automatically, or the tool will return
    status='project_confirmation_needed' for you to confirm first.

    Args:
        file_path: Absolute or relative path to the file to ingest.
        force: Re-ingest even if content hash is unchanged (default False).
        project: Optional project name to assign this document to.
        create_project: Auto-create the project if it doesn't exist (default False).
    """
    path = Path(file_path).resolve()
    if not path.exists():
        return {"status": "error", "message": f"File not found: {path}"}

    try:
        content = parse_document(str(path))
    except Exception as e:
        return {"status": "error", "message": f"Failed to parse document: {str(e)}"}
        
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    filename = path.name

    client = _get_supabase()

    # Check for existing document with same filename
    same_name_result = client.table("documents").select("id, content_hash").eq(
        "filename", filename
    ).execute()

    if same_name_result.data:
        existing = same_name_result.data[0]
        if existing["content_hash"] == content_hash and not force:
            # Same content — skip
            return {
                "status": "skipped",
                "reason": "duplicate",
                "existing_document_id": existing["id"],
                "filename": filename,
            }
        else:
            # Same filename, different hash (or force=True) — delete old and re-ingest
            old_id = existing["id"]
            storage_path = f"documents/{old_id}/{filename}"
            try:
                client.storage.from_("documents").remove([storage_path])
            except Exception:
                pass
            client.table("documents").delete().eq("id", old_id).execute()

    # Create document record
    doc_result = client.table("documents").insert({
        "filename": filename,
        "file_path": str(path),
        "content_hash": content_hash,
        "status": "processing",
    }).execute()

    doc_id = doc_result.data[0]["id"]

    try:
        # Upload raw file to Supabase Storage
        storage_path = f"documents/{doc_id}/{filename}"
        
        # Map file extensions to appropriate MIME types for Supabase Storage
        mime_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".html": "text/html",
            ".md": "text/markdown",
            ".txt": "text/plain"
        }
        content_type = mime_types.get(path.suffix.lower(), "application/octet-stream")
        
        with open(path, "rb") as f:
            client.storage.from_("documents").upload(
                storage_path,
                f.read(),
                {"content-type": content_type},
            )

        # Chunk the content — use structure-aware splitter for Markdown/text
        MARKDOWN_EXTENSIONS = {".md", ".txt"}
        if path.suffix.lower() in MARKDOWN_EXTENSIONS:
            chunks = markdown_split(content)
        else:
            chunks = recursive_split(content)

        if not chunks:
            client.table("documents").update({
                "status": "failed",
            }).eq("id", doc_id).execute()
            return {"status": "error", "message": "No chunks produced from file"}

        # Batch embed all chunks (supports late chunking via EMBEDDING_PROVIDER=jina_late)
        embeddings = embed_chunks_with_context(content, chunks)

        # Insert chunks with embeddings
        chunk_records = []
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_records.append({
                "document_id": doc_id,
                "content": chunk_text,
                "embedding": embedding,
                "chunk_index": i,
                "token_count": len(chunk_text.split()),
            })

        client.table("chunks").insert(chunk_records).execute()

        # Extract metadata
        try:
            metadata = extract_metadata(content)
        except Exception as e:
            # Fallback if LLM extraction completely blows up
            metadata = None
            print(f"Warning: Metadata extraction failed. {e}")

        # Project resolution
        project_name = project or (metadata.project if metadata else None)
        project_id = None
        final_status = "completed"
        response_extra = {}

        if project_name:
            proj = client.table("projects").select("id").eq("name", project_name).execute()
            if proj.data:
                project_id = proj.data[0]["id"]
            elif create_project:
                new_proj = client.table("projects").insert({
                    "name": project_name,
                    "description": f"Auto-created during ingestion of '{filename}'",
                }).execute()
                project_id = new_proj.data[0]["id"]
            else:
                final_status = "project_confirmation_needed"
                response_extra = {
                    "suggested_project": project_name,
                    "action": f"Call ingest_file again with project='{project_name}' and create_project=True.",
                }

        # Update document status and metadata
        update_data = {
            "status": final_status,
            "chunk_count": len(chunks),
            "project_id": project_id,
        }

        if metadata:
            update_data.update({
                "title": metadata.title,
                "summary": metadata.summary,
                "topics": metadata.topics,
                "document_type": metadata.document_type,
                "language": metadata.language,
            })

        client.table("documents").update(update_data).eq("id", doc_id).execute()

        return {
            "status": final_status,
            "document_id": doc_id,
            "filename": filename,
            "chunk_count": len(chunks),
            "content_hash": content_hash,
            "metadata_extracted": metadata is not None,
            "project_id": project_id,
            **response_extra,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        client.table("documents").update({
            "status": "failed",
        }).eq("id", doc_id).execute()
        return {"status": "error", "document_id": doc_id, "message": str(e)}


@mcp.tool()
def list_documents(project: str | None = None) -> list[dict]:
    """List all ingested documents with their status and chunk count.

    Args:
        project: Optional project name to filter documents by.
    """
    client = _get_supabase()
    query = client.table("documents").select(
        "id, filename, status, chunk_count, content_hash, created_at, project_id, projects(id, name)"
    )
    if project:
        proj = client.table("projects").select("id").eq("name", project).execute()
        if proj.data:
            query = query.eq("project_id", proj.data[0]["id"])
        else:
            return []
    result = query.order("created_at", desc=True).execute()
    return result.data


@mcp.tool()
def delete_document(document_id: str) -> dict:
    """Delete a document and all its chunks (cascade delete).

    Args:
        document_id: UUID of the document to delete.
    """
    client = _get_supabase()

    # Get document info first
    doc_result = client.table("documents").select("id, filename").eq(
        "id", document_id
    ).execute()

    if not doc_result.data:
        return {"status": "error", "message": f"Document not found: {document_id}"}

    doc = doc_result.data[0]
    filename = doc["filename"]

    # Delete from storage
    storage_path = f"documents/{document_id}/{filename}"
    try:
        client.storage.from_("documents").remove([storage_path])
    except Exception:
        pass  # File may not exist in storage

    # Delete document (chunks cascade via FK)
    client.table("documents").delete().eq("id", document_id).execute()

    return {
        "deleted": True,
        "document_id": document_id,
        "filename": filename,
    }


@mcp.tool()
def search_documents(
    query: str,
    top_k: int = 5,
    threshold: float = 0.7,
    mode: str = "hybrid",
    rerank: bool = False,
    document_type: str | None = None,
    topics: list[str] | None = None,
    project: str | None = None,
) -> list[dict]:
    """Search ingested documents using vector similarity and optional metadata filters.

    Args:
        query: The search query text.
        top_k: Number of results to return (default 5).
        threshold: Minimum vector similarity score 0-1 (default 0.7).
        mode: Searching mode flag. One of "hybrid", "keyword", or "vector".
        document_type: Filter by a specific document type (e.g., 'article', 'report').
        topics: Filter to documents containing at least one of these topics.
        project: Filter to documents belonging to this project name.
    """
    client = _get_supabase()

    # Resolve project name → UUID
    filter_project_id = None
    if project:
        proj = client.table("projects").select("id").eq("name", project).execute()
        if proj.data:
            filter_project_id = proj.data[0]["id"]
        else:
            return [{"message": f"No project found with name '{project}'."}]

    # Execute Vector Search
    vector_results = []
    if mode in ("hybrid", "vector"):
        try:
            query_embedding = embed_text(query, task_type="RETRIEVAL_QUERY")
            response = client.rpc(
                "search_chunks",
                {
                    "query_embedding": query_embedding,
                    "match_count": top_k * 2 if mode == "hybrid" else top_k,
                    "match_threshold": threshold,
                    "filter_document_type": document_type,
                    "filter_topics": topics,
                    "filter_project_id": filter_project_id,
                }
            ).execute()
            vector_results = response.data
        except Exception as e:
            if mode == "vector":
                return [{"error": f"Failed vector search: {str(e)}"}]
            else:
                print(f"Warning: Vector search failed during hybrid mode: {str(e)}")

    # Execute Keyword Search
    keyword_results = []
    if mode in ("hybrid", "keyword"):
        try:
            response = client.rpc(
                "keyword_search_chunks",
                {
                    "search_query": query,
                    "match_count": top_k * 2 if mode == "hybrid" else top_k,
                    "filter_project_id": filter_project_id,
                }
            ).execute()
            keyword_results = response.data

            # Local metadata filter (document_type / topics) for keyword results
            if document_type or topics:
                def is_match(row):
                    if document_type and row.get("document_type") != document_type:
                        return False
                    if topics and not (set(topics) & set(row.get("topics", []))):
                        return False
                    return True
                keyword_results = [r for r in keyword_results if is_match(r)]

        except Exception as e:
            if mode == "keyword":
                return [{"error": f"Failed keyword search: {str(e)}"}]
            else:
                print(f"Warning: Keyword search failed during hybrid mode: {str(e)}")

    # Fusion + Return Handling
    if mode == "vector":
        results = vector_results
    elif mode == "keyword":
        results = keyword_results
    else:
        results = reciprocal_rank_fusion(vector_results, keyword_results)

    if rerank and results:
        # Pass the top 20 candidates into the cross-encoder just to be safe
        results = rerank_results(query, results[:top_k * 4], top_k=top_k)
    else:
        results = results[:top_k]

    if not results:
        return [{"message": f"No relevant chunks found."}]
        
    return results

@mcp.tool()
def list_projects() -> list[dict]:
    """List all projects with document counts."""
    client = _get_supabase()
    projects = client.table("projects").select("id, name, description, created_at").order(
        "name"
    ).execute()

    if not projects.data:
        return []

    # Attach document counts
    result = []
    for proj in projects.data:
        count_resp = client.table("documents").select(
            "id", count="exact"
        ).eq("project_id", proj["id"]).execute()
        result.append({
            **proj,
            "document_count": count_resp.count or 0,
        })
    return result


@mcp.tool()
def create_project(name: str, description: str = "") -> dict:
    """Create a new project. Returns an error if the name already exists.

    Args:
        name: Unique project name.
        description: Optional description of the project.
    """
    client = _get_supabase()
    existing = client.table("projects").select("id").eq("name", name).execute()
    if existing.data:
        return {"status": "error", "message": f"Project '{name}' already exists.", "id": existing.data[0]["id"]}
    result = client.table("projects").insert({
        "name": name,
        "description": description or None,
    }).execute()
    return {"status": "created", **result.data[0]}


def _get_sql_reader_connection():
    """Get a psycopg2 connection using the read-only role."""
    conn_url = os.getenv("SQL_READER_URL")
    if not conn_url:
        raise ValueError("SQL_READER_URL environment variable is not set")
    return psycopg2.connect(conn_url, cursor_factory=RealDictCursor)


@mcp.tool()
def get_schema() -> list[dict]:
    """Get the database schema (tables, columns, types) for SQL query construction.
    
    Returns:
        List of dictionaries containing table_name, column_name, and data_type
        for all tables in the public schema.
    """
    query = """
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position;
    """
    
    try:
        with _get_sql_reader_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
    except Exception as e:
        return [{"error": f"Failed to fetch schema: {str(e)}"}]


@mcp.tool()
def query_sql(sql: str) -> list[dict]:
    """Execute a read-only SQL query against the database.
    
    This tool is restricted to executing SELECT queries. It uses a dedicated
    read-only Postgres role to ensure safety.

    Args:
        sql: A valid Postgres SQL SELECT query to execute.
    
    Returns:
        A list of rows matching the query, or an error dictionary.
    """
    # Basic injection/intent guardrail on the application layer
    sql_upper = sql.strip().upper()
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        return [{"error": "Only SELECT or WITH queries are permitted."}]
        
    try:
        with _get_sql_reader_connection() as conn:
            # Set a very tight timeout so bad queries don't hang the worker
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout = 10000;") # 10 seconds
                cur.execute(sql)
                results = cur.fetchall()
                
                if not results:
                    return [{"message": "Query returned 0 rows."}]
                return results
    except Exception as e:
        return [{"error": f"Query failed: {str(e)}", "sql": sql}]


if __name__ == "__main__":
    mcp.run(transport="stdio")
