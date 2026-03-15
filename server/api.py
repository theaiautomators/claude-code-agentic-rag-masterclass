import os
import json
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from supabase import create_client, Client
import httpx
import jwt
from jwt.algorithms import ECAlgorithm
from pydantic import BaseModel
import ollama
import tempfile
from fastapi import UploadFile, File

from server.main import search_documents, ingest_file, list_documents, delete_document

SUPABASE_URL = os.getenv("SUPABASE_URL")
# Support both new publishable key format (sb_publishable_*) and legacy JWT anon key
SUPABASE_ANON_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Cache for JWKS public keys (fetched once at startup)
_jwks_cache: dict = {}

async def _get_jwks_key(kid: str, issuer: str):
    global _jwks_cache
    if kid not in _jwks_cache:
        # Derive JWKS URL from the token issuer (e.g. http://127.0.0.1:54321/auth/v1)
        base = issuer.rstrip("/").removesuffix("/auth/v1")
        jwks_url = f"{base}/auth/v1/.well-known/jwks.json"
        async with httpx.AsyncClient() as client:
            resp = await client.get(jwks_url)
            resp.raise_for_status()
            for key_data in resp.json().get("keys", []):
                _jwks_cache[key_data["kid"]] = ECAlgorithm.from_jwk(json.dumps(key_data))
    return _jwks_cache.get(kid)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get authenticated Supabase client for the current user
async def get_supabase_client(authorization: str = Header(None)) -> Client:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.split(" ")[1] if authorization.startswith("Bearer ") else authorization

    # Verify JWT locally using Supabase JWKS (works with both HS256 and ES256)
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        alg = header.get("alg", "HS256")

        issuer = jwt.decode(token, options={"verify_signature": False}).get("iss", "")
        if alg == "ES256" and kid:
            public_key = await _get_jwks_key(kid, issuer)
            if not public_key:
                raise HTTPException(status_code=401, detail="Unknown signing key")
            payload = jwt.decode(token, public_key, algorithms=["ES256"], audience="authenticated")
        else:
            # Legacy HS256 — use JWT secret from env
            jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "super-secret-jwt-token-with-at-least-32-characters-long")
            payload = jwt.decode(token, jwt_secret, algorithms=["HS256"], audience="authenticated")

        # Build a minimal user object from JWT claims
        class _User:
            def __init__(self, p):
                self.id = p["sub"]
                self.email = p.get("email", "")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")

    # Use the Supabase URL from the verified JWT issuer so we hit the right instance
    supabase_base = issuer.rstrip("/").removesuffix("/auth/v1") if issuer else SUPABASE_URL
    client = create_client(supabase_base, SUPABASE_ANON_KEY)
    client.postgrest.auth(token)
    client.user = _User(payload)
    return client

class ChatRequest(BaseModel):
    thread_id: str
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, client: Client = Depends(get_supabase_client)):
    # 1. Save the user's message to the database
    client.table("messages").insert({
        "thread_id": request.thread_id,
        "user_id": client.user.id,
        "role": "user",
        "content": request.message
    }).execute()
    
    # 2. Retrieve context via RAG search (with timeout to avoid blocking on unreachable DB)
    context_texts = []
    try:
        context_results = await asyncio.wait_for(
            asyncio.to_thread(search_documents, request.message, 5),
            timeout=8.0
        )
        if context_results and "error" not in context_results[0] and "message" not in context_results[0]:
            for res in context_results:
                context_texts.append(res.get("content", ""))
    except (asyncio.TimeoutError, Exception):
        pass  # Continue without context if search fails
            
    context_block = "\n---\n".join(context_texts)
    
    # 3. Fetch conversation history for this thread
    history_response = client.table("messages").select("role, content").eq(
        "thread_id", request.thread_id
    ).order("created_at", desc=False).execute()
    
    messages = [
        {"role": "system", "content": f"You are a helpful assistant. Use the following context to answer the user's question. If the answer is not in the context, say you don't know.\n\nContext:\n{context_block}"}
    ]
    
    for msg in history_response.data:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    # 4. Stream response from local Ollama model
    async def generate():
        ollama_client = ollama.AsyncClient()
        response = await ollama_client.chat(
            model='qwen2.5:3b',
            messages=messages,
            stream=True
        )
        
        full_response = ""
        async for chunk in response:
            content = chunk['message']['content']
            full_response += content
            # SSE format
            yield f"data: {json.dumps({'content': content})}\n\n"
            
        # 5. Save the assistant's message to the DB after streaming completes
        if full_response:
             client.table("messages").insert({
                 "thread_id": request.thread_id,
                 "user_id": client.user.id,
                 "role": "assistant",
                 "content": full_response
             }).execute()
             
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

class ThreadCreate(BaseModel):
    title: str

@app.post("/threads")
async def create_thread(req: ThreadCreate, client: Client = Depends(get_supabase_client)):
    res = client.table("threads").insert({
        "user_id": client.user.id,
        "title": req.title
    }).execute()
    return res.data[0]

@app.get("/threads")
async def get_threads(client: Client = Depends(get_supabase_client)):
    res = client.table("threads").select("*").order("created_at", desc=True).execute()
    return res.data

@app.get("/threads/{thread_id}/messages")
async def get_messages(thread_id: str, client: Client = Depends(get_supabase_client)):
    res = client.table("messages").select("*").eq("thread_id", thread_id).order("created_at", desc=False).execute()
    return res.data

@app.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str, client: Client = Depends(get_supabase_client)):
    client.table("threads").delete().eq("id", thread_id).execute()
    return {"status": "deleted"}

@app.post("/ingest")
async def ingest_upload(file: UploadFile = File(...), client: Client = Depends(get_supabase_client)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    
    # Ingest the file using the core function
    res = ingest_file(tmp_path)
    os.remove(tmp_path)
    return res

@app.get("/documents")
async def get_all_documents(client: Client = Depends(get_supabase_client)):
    return list_documents()

@app.delete("/documents/{doc_id}")
async def remove_document(doc_id: str, client: Client = Depends(get_supabase_client)):
    return delete_document(doc_id)
