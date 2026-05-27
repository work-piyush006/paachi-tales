from backend.services.supabase_client import get_supabase_client


def sb():
    return get_supabase_client(service=True)


def list_products(search: str = ""):
    query = sb().table("products").select("*, catalogues(name,slug), product_media(*)")
    if search:
        s = f"%{search}%"
        query = query.or_(f"title.ilike.{s},description.ilike.{s},category.ilike.{s},product_code.ilike.{s}")
    return query.order("created_at", desc=True).execute().data or []


def list_products_by_catalogue(catalogue_id: str):
    return sb().table("products").select("*, product_media(*)").eq("catalogue_id", catalogue_id).order("created_at", desc=True).execute().data or []


def get_product_by_slug(slug: str):
    rows = sb().table("products").select("*, catalogues(name,slug), product_media(*)").eq("slug", slug).limit(1).execute().data or []
    return rows[0] if rows else None


def create_product(payload: dict):
    return sb().table("products").insert(payload).execute().data[0]


def update_product(product_id: str, payload: dict):
    return sb().table("products").update(payload).eq("id", product_id).execute().data[0]


def replace_media(product_id: str, media_records: list[dict]):
    sb().table("product_media").delete().eq("product_id", product_id).execute()
    to_insert = []
    for i, r in enumerate(media_records):
        to_insert.append({"product_id": product_id, "media_url": r["media_url"], "thumb_url": r.get("thumb_url"), "media_type": r["media_type"], "sort_order": i})
    if to_insert:
        sb().table("product_media").insert(to_insert).execute()


def delete_product(product_id: str):
    sb().table("product_media").delete().eq("product_id", product_id).execute()
    sb().table("wishlist").delete().eq("product_id", product_id).execute()
    return sb().table("products").delete().eq("id", product_id).execute()


def wishlist_by_email(email: str):
    u = sb().table("users").select("id").eq("email", email).limit(1).execute().data
    if not u:
        return []
    uid = u[0]["id"]
    rows = sb().table("wishlist").select("products(*)").eq("user_id", uid).execute().data or []
    return [r.get("products") for r in rows if r.get("products")]
