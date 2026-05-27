from flask import Blueprint, render_template, session, request, redirect, url_for, flash, jsonify
from backend.middleware.auth import login_required
from backend.services.content_service import homepage_payload, safe_fetch
from backend.services.supabase_client import get_supabase_client
from backend.middleware.auth import resolve_role
from backend.services.product_service import list_products, get_product_by_slug

web = Blueprint("web", __name__)


@web.route("/")
def home():
    return render_template("pages/home.html", payload=homepage_payload())


@web.route("/collections")
def collections():
    catalogues = safe_fetch("catalogues")
    return render_template("pages/collections.html", collections=catalogues)


@web.route("/collections/<slug>")
def collection_detail(slug):
    collections = safe_fetch("catalogues")
    collection = next((c for c in collections if c.get("slug") == slug), None)
    products = [p for p in list_products() if p.get("catalogue_id") == (collection or {}).get("id")]
    return render_template("pages/collection_detail.html", collection=collection, products=products)


@web.route("/product/<slug>")
def product_detail(slug):
    product = get_product_by_slug(slug)
    if product:
        session.setdefault("recently_viewed", [])
        rv = [item for item in session["recently_viewed"] if item.get("slug") != slug]
        rv.insert(0, {"slug": product.get("slug"), "name": product.get("title") or product.get("name")})
        session["recently_viewed"] = rv[:10]
    return render_template("pages/product_detail.html", product=product)


@web.route('/login')
def login():
    return render_template("pages/login.html")


@web.route('/auth/google/start')
def google_start():
    sb = get_supabase_client()
    callback = url_for('web.auth_callback', _external=True)
    auth = sb.auth.sign_in_with_oauth({"provider": "google", "options": {"redirect_to": callback}})
    return redirect(auth.url)


@web.route('/auth/callback')
def auth_callback():
    email = request.args.get("email", "")
    approved_staff_rows = safe_fetch("admins", "email,is_approved")
    approved_staff = {row["email"] for row in approved_staff_rows if row.get("is_approved")}
    role = resolve_role(email, approved_staff)
    session["user"] = {"email": email, "role": role}
    pending = session.pop("pending_wishlist_slug", None)
    if pending:
        return redirect(url_for('web.wishlist_toggle', slug=pending))
    return redirect(url_for('web.home'))


@web.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('web.home'))


@web.route('/wishlist')
@login_required
def wishlist():
    user_email = session.get("user", {}).get("email")
    items = safe_fetch("wishlist_view") if user_email else []
    return render_template("pages/wishlist.html", items=items)


@web.route('/wishlist/toggle/<slug>', methods=["POST", "GET"])
def wishlist_toggle(slug):
    user = session.get("user")
    if not user:
        session["pending_wishlist_slug"] = slug
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"needsLogin": True}), 401
        return redirect(url_for("web.login"))
    sb = get_supabase_client(service=True)
    product = get_product_by_slug(slug)
    users = sb.table("users").select("id").eq("email", user["email"]).limit(1).execute().data or []
    if not users or not product:
        return jsonify({"error": "Error 404 — Product not found."}), 404
    user_id, product_id = users[0]["id"], product["id"]
    existing = sb.table("wishlist").select("*").eq("user_id", user_id).eq("product_id", product_id).execute().data or []
    if existing:
        sb.table("wishlist").delete().eq("user_id", user_id).eq("product_id", product_id).execute()
    else:
        sb.table("wishlist").insert({"user_id": user_id, "product_id": product_id}).execute()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True})
    return redirect(url_for("web.wishlist"))


@web.route('/search')
def search():
    query = request.args.get("q", "").strip().lower()
    products = list_products(query)
    return render_template("pages/search.html", products=products, query=query)


@web.route('/api/search')
def search_api():
    query = request.args.get("q", "").strip().lower()
    products = list_products(query)[:8]
    return jsonify([{"title": p.get("title") or p.get("name"), "slug": p.get("slug")} for p in products])


@web.route('/recently-viewed')
def recently_viewed():
    return render_template("pages/recently_viewed.html", items=session.get("recently_viewed", []))


@web.route('/about')
def about(): return render_template("pages/about.html")
@web.route('/contact')
def contact(): return render_template("pages/contact.html")
@web.route('/privacy-policy')
def privacy_policy(): return render_template("pages/policy_privacy.html")
@web.route('/shipping-policy')
def shipping_policy(): return render_template("pages/policy_shipping.html")
@web.route('/terms-and-conditions')
def terms_and_conditions(): return render_template("pages/policy_terms.html")
