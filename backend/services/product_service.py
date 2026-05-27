from backend.services.supabase_client import get_supabase_client


def sb():
    return get_supabase_client(service=True)


def list_products(search: str = ""):
    query = sb().table("products").select("*,product_media(*)")
    if search:
        query = query.ilike("title", f"%{search}%")
    return query.order("created_at", desc=True).execute().data or []


def get_product_by_slug(slug: str):
    data = sb().table("products").select("*,product_media(*)").eq("slug", slug).limit(1).execute().data or []
    return data[0] if data else None


def save_product(payload: dict):
    if payload.get("id"):
        return sb().table("products").update(payload).eq("id", payload["id"]).execute().data
    return sb().table("products").insert(payload).execute().data


def add_media(product_id: str, media_urls: list[str], media_type: str):
    records = [{"product_id": product_id, "media_url": u, "media_type": media_type} for u in media_urls]
    if records:
        sb().table("product_media").insert(records).execute()


def delete_product(product_id: str):
    sb().table("product_media").delete().eq("product_id", product_id).execute()
    return sb().table("products").delete().eq("id", product_id).execute()
