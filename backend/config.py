from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str

    # OpenAI (used for embeddings)
    openai_api_key: str

    # OpenRouter (used for LLM chat completions)
    openrouter_api_key: str = ""
    llm_model: str = "gpt-4.1"

    # LangSmith
    langsmith_tracing: str = "true"
    langsmith_api_key: str = ""
    langsmith_project: str = "agentic-rag-masterclass"

    # App
    backend_cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
