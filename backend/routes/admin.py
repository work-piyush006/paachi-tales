from flask import Blueprint, render_template, request, redirect, url_for, flash
from backend.middleware.auth import login_required, role_required
from backend.services.catalog_service import list_catalogues, save_catalogue, delete_catalogue
from backend.services.product_service import list_products, save_product, add_media, delete_product
from backend.services.media_service import upload_media
from backend.services.content_service import safe_fetch

admin = Blueprint("admin", __name__, url_prefix="/hidden-admin")


@admin.route("/")
@login_required
@role_required("super_admin", "staff_admin")
def dashboard():
    return render_template("pages/admin/dashboard.html", products=list_products(), catalogues=list_catalogues(), staff=safe_fetch("admins"))


@admin.route("/catalogue/save", methods=["POST"])
@login_required
@role_required("super_admin", "staff_admin")
def catalogue_save():
    payload = {
        "id": request.form.get("id") or None,
        "name": request.form.get("name", "").strip(),
        "slug": request.form.get("slug", "").strip(),
        "description": request.form.get("description", "").strip(),
        "cover_image_url": request.form.get("cover_image_url", "").strip(),
    }
    save_catalogue(payload)
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
    payload = {
        "id": request.form.get("id") or None,
        "title": request.form.get("title", "").strip(),
        "name": request.form.get("title", "").strip(),
        "slug": request.form.get("slug", "").strip(),
        "description": request.form.get("description", "").strip(),
        "product_code": request.form.get("product_code", "").strip(),
        "category": request.form.get("category", "").strip(),
        "catalogue_id": request.form.get("catalogue_id") or None,
    }
    record = save_product(payload)
    product_id = (record[0] if record else {}).get("id")

    images = request.files.getlist("images")
    videos = request.files.getlist("videos")
    image_urls = upload_media([f for f in images if f.filename], "image") if images and images[0].filename else []
    video_urls = upload_media([f for f in videos if f.filename], "video") if videos and videos[0].filename else []
    if image_urls and product_id:
        add_media(product_id, image_urls, "image")
        save_product({"id": product_id, "hero_image_url": image_urls[0], "thumbnail_url": image_urls[0]})
    if video_urls and product_id:
        add_media(product_id, video_urls, "video")

    flash("Product saved.", "success")
    return redirect(url_for("admin.dashboard"))


@admin.route("/product/delete/<product_id>", methods=["POST"])
@login_required
@role_required("super_admin", "staff_admin")
def product_delete(product_id):
    delete_product(product_id)
    flash("Product deleted.", "success")
    return redirect(url_for("admin.dashboard"))
