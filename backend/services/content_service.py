from backend.services.supabase_client import get_supabase_client


def safe_fetch(table: str, query: str = "*"):
    try:
        sb = get_supabase_client()
        return sb.table(table).select(query).execute().data or []
    except Exception:
        return []


def homepage_payload():
    return {
        "banners": safe_fetch("banners"),
        "featured_collections": safe_fetch("catalogues", "id,name,slug,description,cover_image_url"),
        "featured_products": safe_fetch("products", "id,name,slug,price_inr,hero_image_url,is_featured")[:6],
        "sections": safe_fetch("homepage_sections", "id,title,subtitle,body,order_index")
    }
