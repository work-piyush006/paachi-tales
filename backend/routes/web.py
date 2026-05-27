from flask import Blueprint, render_template, session, request, redirect, url_for, jsonify
from backend.middleware.auth import login_required
from backend.services.content_service import homepage_payload, safe_fetch
from backend.services.supabase_client import get_supabase_client
from backend.middleware.auth import resolve_role
from backend.services.product_service import list_products, get_product_by_slug, list_products_by_catalogue, wishlist_by_email
from backend.services.catalog_service import list_catalogues, get_catalogue_by_slug

web = Blueprint("web", __name__)

@web.route("/")
def home():
    payload = homepage_payload(); payload["featured_products"] = list_products()[:6]
    return render_template("pages/home.html", payload=payload)

@web.route("/collections")
def collections(): return render_template("pages/collections.html", collections=list_catalogues())

@web.route("/collections/<slug>")
def collection_detail(slug):
    c = get_catalogue_by_slug(slug)
    return render_template("pages/collection_detail.html", collection=c, products=list_products_by_catalogue(c["id"]) if c else [])

@web.route("/product/<slug>")
def product_detail(slug):
    p = get_product_by_slug(slug)
    if p:
        rv = session.get("recently_viewed", [])
        rv = [x for x in rv if x.get("slug") != slug]
        rv.insert(0, {"slug": p["slug"], "name": p.get("title") or p.get("name"), "thumbnail_url": p.get("thumbnail_url") or p.get("hero_image_url")})
        session["recently_viewed"] = rv[:16]
        session.permanent = True
    return render_template("pages/product_detail.html", product=p)

@web.route('/login')
def login(): return render_template("pages/login.html")

@web.route('/auth/google/start')
def google_start():
    sb = get_supabase_client(); callback = url_for('web.auth_callback', _external=True)
    return redirect(sb.auth.sign_in_with_oauth({"provider":"google","options":{"redirect_to":callback}}).url)

@web.route('/auth/callback')
def auth_callback():
    email = request.args.get("email", "")
    approved_staff = {r["email"] for r in safe_fetch("admins","email,is_approved") if r.get("is_approved")}
    session["user"] = {"email": email, "role": resolve_role(email, approved_staff)}
    session.permanent = True
    pending = session.pop("pending_wishlist_slug", None)
    return redirect(url_for('web.wishlist_toggle', slug=pending) if pending else url_for('web.home'))

@web.route('/logout')
def logout(): session.clear(); return redirect(url_for('web.home'))

@web.route('/wishlist')
@login_required
def wishlist(): return render_template("pages/wishlist.html", items=wishlist_by_email(session["user"]["email"]))

@web.route('/wishlist/toggle/<slug>', methods=['POST','GET'])
def wishlist_toggle(slug):
    user = session.get("user")
    if not user:
        session["pending_wishlist_slug"] = slug
        return (jsonify({"needsLogin":True}),401) if request.headers.get("X-Requested-With")=="XMLHttpRequest" else redirect(url_for("web.login"))
    sb = get_supabase_client(service=True); p = get_product_by_slug(slug)
    u = sb.table("users").select("id").eq("email", user["email"]).limit(1).execute().data or []
    if not u:
        created = sb.table("users").insert({"email": user["email"]}).execute().data or []
        u = created
    if not u or not p: return jsonify({"error":"Error 404 — Product not found."}),404
    uid,pid = u[0]["id"],p["id"]
    ex = sb.table("wishlist").select("*").eq("user_id",uid).eq("product_id",pid).execute().data or []
    (sb.table("wishlist").delete().eq("user_id",uid).eq("product_id",pid).execute() if ex else sb.table("wishlist").insert({"user_id":uid,"product_id":pid}).execute())
    return jsonify({"ok":True,"saved":not bool(ex)}) if request.headers.get("X-Requested-With")=="XMLHttpRequest" else redirect(url_for("web.wishlist"))

@web.route('/search')
def search():
    q = request.args.get("q", "").strip().lower()
    products = list_products(q)
    if q:
        names = {c["id"]: c["name"].lower() for c in list_catalogues()}
        products = [p for p in products if q in (p.get("title") or "").lower() or q in (p.get("description") or "").lower() or q in (p.get("category") or "").lower() or q in names.get(p.get("catalogue_id"), "")]
    return render_template("pages/search.html", products=products, query=q)

@web.route('/api/search')
def search_api():
    q=request.args.get("q","")
    return jsonify([{"title":p.get("title") or p.get("name"),"slug":p.get("slug"),"thumb":p.get("thumbnail_url") or p.get("hero_image_url")} for p in list_products(q)[:8]])

@web.route('/recently-viewed')
def recently_viewed(): return render_template("pages/recently_viewed.html", items=session.get("recently_viewed", []))
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
