import json
from typing import AsyncGenerator

from langsmith import traceable

from config import settings
from services.openai_client import get_llm_client
from services.thread_service import ThreadService
from services.retrieval_service import RetrievalService

SYSTEM_PROMPT = (
    "You are a helpful RAG assistant. You answer questions clearly and concisely. "
    "When you don't know the answer, say so honestly.\n\n"
    "You have access to the user's uploaded documents. When a question might be "
    "answered by their documents, use the search_documents tool to find relevant "
    "information. When citing information from documents, mention the source filename."
)

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": "Search the user's uploaded documents for relevant information. Use this when the user asks about content that might be in their documents.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant document chunks",
                },
            },
            "required": ["query"],
        },
    },
}


class ChatService:
    def __init__(self, user_id: str):
        self.llm = get_llm_client()
        self.thread_service = ThreadService(user_id)
        self.retrieval = RetrievalService(user_id)
        self.user_id = user_id

    @traceable(name="chat_stream_response", run_type="chain")
    async def stream_response(
        self,
        thread_id: str,
        content: str,
    ) -> AsyncGenerator[dict, None]:
        # 1. Save user message
        self.thread_service.save_message(
            thread_id=thread_id,
            role="user",
            content=content,
        )

        # 2. Fetch ALL messages from DB to build conversation history
        db_messages = self.thread_service.list_messages(thread_id)

        # 3. Build messages array: system prompt + full history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in db_messages:
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })

        # 4. First LLM call (non-streaming) with tool available
        full_text = ""
        token_usage = None

        try:
            first_response = self.llm.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                tools=[SEARCH_TOOL],
            )
        except Exception as e:
            error_msg = str(e)
            # Extract readable error from OpenAI API errors
            if "402" in error_msg:
                error_msg = "LLM provider returned 402: insufficient credits. Please add credits at https://openrouter.ai/settings/credits"
            yield {
                "event": "error",
                "data": json.dumps({"message": error_msg}),
            }
            return

        choice = first_response.choices[0]

        print(f"[RAG] Tool calls: {choice.message.tool_calls}")
        if choice.message.tool_calls:
            # 5a. Tool was called — execute search and make second call
            tool_call = choice.message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            query = args.get("query", content)

            # Execute search
            print(f"[RAG] Tool called with query: {query!r} for user: {self.user_id}")
            results = self.retrieval.search(query)
            print(f"[RAG] Search returned {len(results)} results")
            for r in results:
                print(f"[RAG]   similarity={r.get('similarity', '?'):.4f}  filename={r.get('filename', '?')}")

            # Format results for the LLM
            if results:
                context_parts = []
                for r in results:
                    context_parts.append(
                        f"[From: {r['filename']}] (similarity: {r['similarity']:.2f})\n{r['content']}"
                    )
                tool_result = "\n\n---\n\n".join(context_parts)
            else:
                tool_result = "No relevant documents found."

            # Append assistant message with tool call + tool result
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                ],
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result,
            })

            # Second LLM call — streaming, no tools
            stream = self.llm.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                stream=True,
                stream_options={"include_usage": True},
            )

            for chunk in stream:
                if chunk.usage:
                    token_usage = {
                        "input_tokens": chunk.usage.prompt_tokens,
                        "output_tokens": chunk.usage.completion_tokens,
                        "total_tokens": chunk.usage.total_tokens,
                    }

                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    full_text += delta
                    yield {
                        "event": "text_delta",
                        "data": json.dumps({"content": delta}),
                    }
        else:
            # 5b. No tool call — yield the response content directly
            if choice.message.content:
                full_text = choice.message.content
                yield {
                    "event": "text_delta",
                    "data": json.dumps({"content": full_text}),
                }

            if first_response.usage:
                token_usage = {
                    "input_tokens": first_response.usage.prompt_tokens,
                    "output_tokens": first_response.usage.completion_tokens,
                    "total_tokens": first_response.usage.total_tokens,
                }

        # 6. Save assistant message
        save_kwargs = {}
        if token_usage:
            save_kwargs["token_usage"] = json.dumps(token_usage)
        self.thread_service.save_message(
            thread_id=thread_id,
            role="assistant",
            content=full_text,
            **save_kwargs,
        )

        # 7. Signal done
        yield {
            "event": "done",
            "data": json.dumps({}),
        }
