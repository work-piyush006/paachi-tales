from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from backend.middleware.auth import login_required, role_required
from backend.services.catalog_service import list_catalogues, save_catalogue, delete_catalogue
from backend.services.product_service import list_products, create_product, update_product, delete_product, get_product_by_slug, replace_media
from backend.services.media_service import upload_images, upload_videos, persist_url_media
from backend.services.content_service import safe_fetch
from backend.services.supabase_client import get_supabase_client

admin = Blueprint("admin", __name__, url_prefix="/hidden-admin")


def is_super_admin():
    return session.get("user", {}).get("role") == "super_admin"


@admin.route("/")
@login_required
@role_required("super_admin", "staff_admin")
def dashboard():
    products = list_products()
    catalogues = list_catalogues()
    banners = safe_fetch("banners")
    sections = safe_fetch("homepage_sections")
    staff = safe_fetch("admins")
    stats = {
        "products": len(products), "catalogues": len(catalogues), "banners": len(banners),
        "staff": len(staff), "featured": len([p for p in products if p.get("is_featured")])
    }
    return render_template("pages/admin/dashboard.html", products=products, catalogues=catalogues, banners=banners, sections=sections, staff=staff, stats=stats, can_manage_staff=is_super_admin())


@admin.route("/catalogue/save", methods=["POST"])
@login_required
@role_required("super_admin", "staff_admin")
def catalogue_save():
    save_catalogue({"id": request.form.get("id") or None, "name": request.form["name"].strip(), "slug": request.form["slug"].strip(), "description": request.form.get("description", "").strip(), "cover_image_url": request.form.get("cover_image_url", "").strip()})
    flash("Catalogue saved.", "success")
    return redirect(url_for("admin.dashboard"))


@admin.route("/catalogue/delete/<catalogue_id>", methods=["POST"])
@login_required
@role_required("super_admin", "staff_admin")
def catalogue_delete(catalogue_id):
    delete_catalogue(catalogue_id)
    flash("Catalogue deleted.", "success")
    return redirect(url_for("admin.dashboard"))


@admin.route("/product/save", methods=["POST"])
@login_required
@role_required("super_admin", "staff_admin")
def product_save():
    pid = request.form.get("id")
    payload = {"title": request.form["title"].strip(), "name": request.form["title"].strip(), "slug": request.form["slug"].strip(), "description": request.form.get("description", "").strip(), "product_code": request.form["product_code"].strip(), "category": request.form.get("category", "").strip(), "catalogue_id": request.form.get("catalogue_id") or None}
    product = update_product(pid, payload) if pid else create_product(payload)

    media = []
    image_files = [f for f in request.files.getlist("images") if f and f.filename]
    video_files = [f for f in request.files.getlist("videos") if f and f.filename]
    if image_files: media.extend(upload_images(image_files))
    if video_files: media.extend(upload_videos(video_files))
    media.extend(persist_url_media(request.form.get("image_urls", "").splitlines(), "image"))
    media.extend(persist_url_media(request.form.get("video_urls", "").splitlines(), "video"))

    if media:
        replace_media(product["id"], media)
        first_image = next((m for m in media if m["media_type"] == "image"), None)
        if first_image:
            update_product(product["id"], {"thumbnail_url": first_image.get("thumb_url") or first_image["media_url"], "hero_image_url": first_image["media_url"]})
    flash("Product saved.", "success")
    return redirect(url_for("admin.dashboard"))


@admin.route('/product/edit/<slug>')
@login_required
@role_required("super_admin", "staff_admin")
def product_edit(slug):
    return render_template("pages/admin/product_edit.html", product=get_product_by_slug(slug), catalogues=list_catalogues())


@admin.route('/product/delete/<product_id>', methods=['POST'])
@login_required
@role_required("super_admin", "staff_admin")
def product_delete_route(product_id):
    delete_product(product_id)
    flash("Product deleted.", "success")
    return redirect(url_for('admin.dashboard'))


@admin.route('/banner/save', methods=['POST'])
@login_required
@role_required("super_admin", "staff_admin")
def banner_save():
    sb = get_supabase_client(service=True)
    payload = {"id": request.form.get("id") or None, "title": request.form.get("title", ""), "subtitle": request.form.get("subtitle", ""), "image_url": request.form.get("image_url", ""), "video_url": request.form.get("video_url", ""), "cta_label": request.form.get("cta_label", "Explore"), "cta_url": request.form.get("cta_url", "/collections"), "is_active": request.form.get("is_active") == "on"}
    if payload["id"]: sb.table("banners").update(payload).eq("id", payload["id"]).execute()
    else: sb.table("banners").insert(payload).execute()
    flash("Banner saved.", "success")
    return redirect(url_for('admin.dashboard'))


@admin.route('/banner/delete/<banner_id>', methods=['POST'])
@login_required
@role_required("super_admin", "staff_admin")
def banner_delete(banner_id):
    get_supabase_client(service=True).table("banners").delete().eq("id", banner_id).execute()
    flash("Banner deleted.", "success")
    return redirect(url_for('admin.dashboard'))

@admin.route('/section/save', methods=['POST'])
@login_required
@role_required("super_admin", "staff_admin")
def section_save():
    sb = get_supabase_client(service=True)
    payload = {"id": request.form.get("id") or None, "title": request.form.get("title", ""), "subtitle": request.form.get("subtitle", ""), "body": request.form.get("body", ""), "order_index": int(request.form.get("order_index", "0") or 0), "is_active": request.form.get("is_active") == "on"}
    if payload["id"]: sb.table("homepage_sections").update(payload).eq("id", payload["id"]).execute()
    else: sb.table("homepage_sections").insert(payload).execute()
    flash("Homepage section saved.", "success")
    return redirect(url_for('admin.dashboard'))


@admin.route('/section/delete/<section_id>', methods=['POST'])
@login_required
@role_required("super_admin", "staff_admin")
def section_delete(section_id):
    get_supabase_client(service=True).table("homepage_sections").delete().eq("id", section_id).execute()
    flash("Homepage section deleted.", "success")
    return redirect(url_for('admin.dashboard'))


@admin.route('/staff/save', methods=['POST'])
@login_required
@role_required("super_admin")
def staff_save():
    sb = get_supabase_client(service=True)
    email = request.form.get("email", "").strip().lower()
    payload = {"email": email, "is_approved": request.form.get("is_approved") == "on", "designation": request.form.get("designation", "").strip(), "name": request.form.get("name", "").strip()}
    existing = sb.table("admins").select("id").eq("email", email).limit(1).execute().data or []
    if existing:
        sb.table("admins").update(payload).eq("id", existing[0]["id"]).execute()
    else:
        sb.table("admins").insert(payload).execute()
    flash("Staff admin saved.", "success")
    return redirect(url_for('admin.dashboard'))


@admin.route('/staff/delete/<staff_id>', methods=['POST'])
@login_required
@role_required("super_admin")
def staff_delete(staff_id):
    get_supabase_client(service=True).table("admins").delete().eq("id", staff_id).execute()
    flash("Staff removed.", "success")
    return redirect(url_for('admin.dashboard'))
