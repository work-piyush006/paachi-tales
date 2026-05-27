from backend.services.supabase_client import get_supabase_client


def sb():
    return get_supabase_client(service=True)


def list_catalogues():
    return sb().table("catalogues").select("*").order("name").execute().data or []


def get_catalogue_by_slug(slug: str):
    rows = sb().table("catalogues").select("*").eq("slug", slug).limit(1).execute().data or []
    return rows[0] if rows else None


def save_catalogue(payload: dict):
    if payload.get("id"):
        return sb().table("catalogues").update(payload).eq("id", payload["id"]).execute().data[0]
    return sb().table("catalogues").insert(payload).execute().data[0]


def delete_catalogue(catalogue_id: str):
    sb().table("products").update({"catalogue_id": None}).eq("catalogue_id", catalogue_id).execute()
    return sb().table("catalogues").delete().eq("id", catalogue_id).execute()
