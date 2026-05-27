import mimetypes
import uuid
from io import BytesIO
from pathlib import Path
from PIL import Image
from werkzeug.datastructures import FileStorage
from backend.config.settings import settings
from backend.services.supabase_client import get_supabase_client

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
IMAGES_BUCKET = "product-images"
VIDEOS_BUCKET = "product-videos"
ALLOWED_IMAGE = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_VIDEO = {"video/mp4", "video/webm", "video/quicktime"}


def _guess_type(url: str) -> str:
    mt, _ = mimetypes.guess_type(url)
    return mt or "application/octet-stream"


def _upload_to_supabase(bucket: str, blob: bytes, path: str, content_type: str):
    sb = get_supabase_client(service=True)
    sb.storage.from_(bucket).upload(path, blob, {"content-type": content_type, "upsert": "true"})
    return sb.storage.from_(bucket).get_public_url(path)


def _store_local(blob: bytes, folder: str, name: str) -> str:
    target = UPLOAD_DIR / folder
    target.mkdir(parents=True, exist_ok=True)
    p = target / name
    p.write_bytes(blob)
    return f"/{p.as_posix()}"


def image_to_webp(file: FileStorage):
    img = Image.open(file.stream).convert("RGB")
    img.thumbnail((1800, 1800))
    full = BytesIO(); img.save(full, "WEBP", quality=84, method=6)
    thumb = img.copy(); thumb.thumbnail((540, 540))
    mini = BytesIO(); thumb.save(mini, "WEBP", quality=78, method=6)
    return full.getvalue(), mini.getvalue()


def persist_url_media(urls: list[str], media_type: str):
    out = []
    for url in urls:
        u = (url or "").strip()
        if not u:
            continue
        if media_type == "image" and _guess_type(u) not in ALLOWED_IMAGE:
            continue
        if media_type == "video" and _guess_type(u) not in ALLOWED_VIDEO:
            continue
        out.append({"media_url": u, "media_type": media_type, "thumb_url": u if media_type == "image" else None})
    return out


def upload_images(files: list[FileStorage]):
    if not (1 <= len(files) <= 10):
        raise ValueError("Error 422 — Upload 1 to 10 images.")
    saved = []
    use_supabase = bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)
    for f in files:
        if f.mimetype not in ALLOWED_IMAGE:
            raise ValueError("Error 413 — Unsupported image format.")
        full, thumb = image_to_webp(f)
        name = f"{uuid.uuid4().hex}.webp"
        tname = f"thumb-{name}"
        if use_supabase:
            full_url = _upload_to_supabase(IMAGES_BUCKET, full, name, "image/webp")
            thumb_url = _upload_to_supabase(IMAGES_BUCKET, thumb, tname, "image/webp")
        else:
            full_url = _store_local(full, "images", name)
            thumb_url = _store_local(thumb, "images", tname)
        saved.append({"media_url": full_url, "thumb_url": thumb_url, "media_type": "image"})
    return saved


def upload_videos(files: list[FileStorage]):
    if not (1 <= len(files) <= 3):
        raise ValueError("Error 422 — Upload 1 to 3 videos.")
    saved = []
    use_supabase = bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)
    for f in files:
        if f.mimetype not in ALLOWED_VIDEO:
            raise ValueError("Error 413 — Unsupported video format.")
        blob = f.read()
        if len(blob) > 70 * 1024 * 1024:
            raise ValueError("Error 413 — Media file too large.")
        ext = Path(f.filename or "video.mp4").suffix or ".mp4"
        name = f"{uuid.uuid4().hex}{ext}"
        if use_supabase:
            url = _upload_to_supabase(VIDEOS_BUCKET, blob, name, f.mimetype)
        else:
            url = _store_local(blob, "videos", name)
        saved.append({"media_url": url, "media_type": "video", "thumb_url": None})
    return saved
