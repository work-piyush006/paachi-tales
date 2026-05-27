from supabase import create_client, Client
from backend.config.settings import settings


def get_supabase_client(service: bool = False) -> Client:
    key = settings.SUPABASE_SERVICE_ROLE_KEY if service else settings.SUPABASE_ANON_KEY
    if not settings.SUPABASE_URL or not key:
        raise RuntimeError("Supabase credentials are not configured")
    return create_client(settings.SUPABASE_URL, key)
