import json
from typing import AsyncGenerator

from langsmith import traceable

from services.openai_client import get_openai_client
from services.thread_service import ThreadService


class ChatService:
    def __init__(self, user_id: str):
        self.openai = get_openai_client()
        self.thread_service = ThreadService(user_id)
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

        # 2. Get thread's previous response ID for conversation continuity
        thread = self.thread_service.get_thread(thread_id)
        previous_response_id = thread.get("openai_response_id") if thread else None

        # 3. Call OpenAI Responses API with streaming
        full_text = ""
        response_id = None
        token_usage = None

        stream = self.openai.responses.create(
            model="gpt-4.1",
            input=content,
            previous_response_id=previous_response_id,
            store=True,
            stream=True,
        )

        for event in stream:
            if event.type == "response.output_text.delta":
                full_text += event.delta
                yield {
                    "event": "text_delta",
                    "data": json.dumps({"content": event.delta}),
                }
            elif event.type == "response.completed":
                response_id = event.response.id
                if event.response.usage:
                    token_usage = {
                        "input_tokens": event.response.usage.input_tokens,
                        "output_tokens": event.response.usage.output_tokens,
                        "total_tokens": event.response.usage.total_tokens,
                    }

        # 4. Save assistant message
        self.thread_service.save_message(
            thread_id=thread_id,
            role="assistant",
            content=full_text,
            openai_response_id=response_id,
            token_usage=token_usage,
        )

        # 5. Update thread with latest response ID
        self.thread_service.update_thread(
            thread_id=thread_id,
            updates={"openai_response_id": response_id},
        )

        # 6. Signal done
        yield {
            "event": "done",
            "data": json.dumps({"response_id": response_id}),
        }
