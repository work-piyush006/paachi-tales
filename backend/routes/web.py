from flask import Blueprint, render_template, session, request, redirect, url_for
from backend.middleware.auth import login_required
from backend.services.content_service import homepage_payload, safe_fetch
from backend.services.supabase_client import get_supabase_client
from backend.middleware.auth import resolve_role

web = Blueprint("web", __name__)


def find_by_slug(table: str, slug: str):
    rows = safe_fetch(table)
    for row in rows:
        if row.get("slug") == slug:
            return row
    return None


@web.route("/")
def home():
    return render_template("pages/home.html", payload=homepage_payload())


@web.route("/collections")
def collections():
    return render_template("pages/collections.html", collections=safe_fetch("catalogues"))


@web.route("/collections/<slug>")
def collection_detail(slug):
    collection = find_by_slug("catalogues", slug)
    products = safe_fetch("products")
    return render_template("pages/collection_detail.html", collection=collection, products=products)


@web.route("/product/<slug>")
def product_detail(slug):
    product = find_by_slug("products", slug)
    if product:
        session.setdefault("recently_viewed", [])
        rv = [item for item in session["recently_viewed"] if item.get("slug") != slug]
        rv.insert(0, {"slug": product.get("slug"), "name": product.get("name")})
        session["recently_viewed"] = rv[:10]
    return render_template("pages/product_detail.html", product=product)


@web.route("/wishlist")
@login_required
def wishlist():
    return render_template("pages/wishlist.html", items=safe_fetch("wishlist"))


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
    return redirect(url_for('web.home'))


@web.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('web.home'))


@web.route('/search')
def search():
    query = request.args.get("q", "").lower().strip()
    products = [p for p in safe_fetch("products") if query in p.get("name", "").lower()]
    return render_template("pages/search.html", products=products, query=query)


@web.route('/recently-viewed')
def recently_viewed():
    return render_template("pages/recently_viewed.html", items=session.get("recently_viewed", []))


@web.route('/about')
def about():
    return render_template("pages/about.html")


@web.route('/contact')
def contact():
    return render_template("pages/contact.html")


@web.route('/privacy-policy')
def privacy_policy():
    return render_template("pages/policy_privacy.html")


@web.route('/shipping-policy')
def shipping_policy():
    return render_template("pages/policy_shipping.html")


@web.route('/terms-and-conditions')
def terms_and_conditions():
    return render_template("pages/policy_terms.html")
