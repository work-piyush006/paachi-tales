from backend.services.supabase_client import get_supabase_client


def sb():
    return get_supabase_client(service=True)


def list_catalogues():
    return sb().table("catalogues").select("*").order("name").execute().data or []


def save_catalogue(payload: dict):
    if payload.get("id"):
        return sb().table("catalogues").update(payload).eq("id", payload["id"]).execute().data
    return sb().table("catalogues").insert(payload).execute().data


def delete_catalogue(catalogue_id: str):
    return sb().table("catalogues").delete().eq("id", catalogue_id).execute()
