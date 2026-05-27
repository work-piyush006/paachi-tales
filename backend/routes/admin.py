from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from backend.middleware.auth import login_required, role_required
from backend.services.catalog_service import list_catalogues, save_catalogue, delete_catalogue
from backend.services.product_service import list_products, create_product, update_product, delete_product, get_product_by_slug, replace_media
from backend.services.media_service import upload_images, upload_videos, persist_url_media
from backend.services.content_service import safe_fetch

admin = Blueprint("admin", __name__, url_prefix="/hidden-admin")


def can_manage_staff():
    return session.get("user", {}).get("role") == "super_admin"


@admin.route("/")
@login_required
@role_required("super_admin", "staff_admin")
def dashboard():
    prods = list_products()
    cats = list_catalogues()
    return render_template("pages/admin/dashboard.html", products=prods, catalogues=cats, staff=safe_fetch("admins"), banners=safe_fetch("banners"), can_manage_staff=can_manage_staff())


@admin.route("/catalogue/save", methods=["POST"])
@login_required
@role_required("super_admin", "staff_admin")
def catalogue_save():
    payload = {"id": request.form.get("id") or None, "name": request.form["name"].strip(), "slug": request.form["slug"].strip(), "description": request.form.get("description", "").strip(), "cover_image_url": request.form.get("cover_image_url", "").strip()}
    save_catalogue(payload)
    flash("Catalogue saved.", "success")
    return redirect(url_for("admin.dashboard"))


@admin.route("/catalogue/delete/<catalogue_id>", methods=["POST"])
@login_required
@role_required("super_admin", "staff_admin")
def catalogue_delete(catalogue_id):
    delete_catalogue(catalogue_id); flash("Catalogue deleted.", "success")
    return redirect(url_for("admin.dashboard"))


@admin.route("/product/save", methods=["POST"])
@login_required
@role_required("super_admin", "staff_admin")
def product_save():
    pid = request.form.get("id")
    payload = {"title": request.form["title"].strip(), "name": request.form["title"].strip(), "slug": request.form["slug"].strip(), "description": request.form.get("description", "").strip(), "product_code": request.form["product_code"].strip(), "category": request.form.get("category", "").strip(), "catalogue_id": request.form.get("catalogue_id") or None}

    p = update_product(pid, payload) if pid else create_product(payload)
    image_files = [f for f in request.files.getlist("images") if f and f.filename]
    video_files = [f for f in request.files.getlist("videos") if f and f.filename]
    image_urls = [u.strip() for u in request.form.get("image_urls", "").splitlines() if u.strip()]
    video_urls = [u.strip() for u in request.form.get("video_urls", "").splitlines() if u.strip()]
    media = []
    if image_files: media.extend(upload_images(image_files))
    if video_files: media.extend(upload_videos(video_files))
    media.extend(persist_url_media(image_urls, "image"))
    media.extend(persist_url_media(video_urls, "video"))

    existing = get_product_by_slug(p["slug"]) or {}
    old_media = existing.get("product_media", [])
    if media:
        replace_media(p["id"], media)
        first_img = next((m for m in media if m["media_type"] == "image"), None)
        if first_img:
            update_product(p["id"], {"thumbnail_url": first_img.get("thumb_url") or first_img["media_url"], "hero_image_url": first_img["media_url"]})
    elif old_media:
        pass
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
    delete_product(product_id); flash("Product deleted.", "success")
    return redirect(url_for('admin.dashboard'))
