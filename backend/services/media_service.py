import io
import os
import uuid
from pathlib import Path
from PIL import Image
from werkzeug.datastructures import FileStorage
from backend.config.settings import settings
from backend.services.supabase_client import get_supabase_client

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_IMAGE = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_VIDEO = {"video/mp4", "video/webm", "video/quicktime"}


def _save_local(file: FileStorage, folder: str) -> str:
    ext = Path(file.filename or "").suffix.lower() or ".bin"
    name = f"{uuid.uuid4().hex}{ext}"
    target = UPLOAD_DIR / folder
    target.mkdir(parents=True, exist_ok=True)
    path = target / name
    file.save(path)
    return f"/{path.as_posix()}"


def _to_webp(file: FileStorage, folder: str) -> str:
    img = Image.open(file.stream).convert("RGB")
    img.thumbnail((1600, 1600))
    name = f"{uuid.uuid4().hex}.webp"
    target = UPLOAD_DIR / folder
    target.mkdir(parents=True, exist_ok=True)
    path = target / name
    img.save(path, "WEBP", quality=84, method=6)
    return f"/{path.as_posix()}"


def upload_media(files, media_type: str):
    urls = []
    if media_type == "image" and not (1 <= len(files) <= 10):
        raise ValueError("Error 422 — Upload 1 to 10 images.")
    if media_type == "video" and not (1 <= len(files) <= 3):
        raise ValueError("Error 422 — Upload 1 to 3 videos.")

    sb = None
    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
        sb = get_supabase_client(service=True)

    for file in files:
        if not file or not file.filename:
            continue
        if media_type == "image" and file.mimetype not in ALLOWED_IMAGE:
            raise ValueError("Error 413 — Unsupported image format.")
        if media_type == "video" and file.mimetype not in ALLOWED_VIDEO:
            raise ValueError("Error 413 — Unsupported video format.")

        local_url = _to_webp(file, "images") if media_type == "image" else _save_local(file, "videos")
        urls.append(local_url)

    return urls
