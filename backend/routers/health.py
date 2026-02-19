from fastapi import APIRouter

from config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/health/services")
async def service_health():
    return {
        "openai": {
            "configured": bool(settings.openai_api_key),
        },
        "langsmith": {
            "enabled": settings.langsmith_tracing.lower() == "true" and bool(settings.langsmith_api_key),
            "project": settings.langsmith_project,
        },
        "supabase": {
            "configured": bool(settings.supabase_url) and bool(settings.supabase_service_role_key),
            "url": settings.supabase_url,
        },
    }
