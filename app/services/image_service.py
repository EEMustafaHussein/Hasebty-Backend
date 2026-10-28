"""Pictures that staff upload from the dashboard."""

import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

MAX_IMAGE_BYTES = 2 * 1024 * 1024  # 2 MB
UPLOAD_URL_PREFIX = "/uploads/parts/"
# The project folder: /code in Docker, so the default is /code/uploads.
DEFAULT_UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"


def upload_root() -> Path:
    """Where uploaded files are kept. On the server this folder must be a backed-up volume."""
    return Path(os.getenv("UPLOAD_DIR") or DEFAULT_UPLOAD_DIR)


def image_extension(data: bytes) -> str | None:
    """Look at the first bytes of the file, not at its name: only real PNG, JPG or WEBP pass."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def save_part_image(part_id: int, file: UploadFile) -> str:
    """Save the uploaded picture and return its path, e.g. /uploads/parts/part-3-1a2b3c4d.png."""
    data = file.file.read(MAX_IMAGE_BYTES + 1)
    if not data:
        raise HTTPException(status_code=422, detail="The image file is empty")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=422, detail="The image must be 2 MB or smaller")

    extension = image_extension(data)
    if extension is None:
        raise HTTPException(status_code=422, detail="The image must be a PNG, JPG or WEBP file")

    folder = upload_root() / "parts"
    folder.mkdir(parents=True, exist_ok=True)
    name = f"part-{part_id}-{uuid.uuid4().hex[:8]}{extension}"
    (folder / name).write_bytes(data)
    return UPLOAD_URL_PREFIX + name


def delete_uploaded_image(image_url: str | None) -> None:
    """Remove an old uploaded picture. Category pictures and outside links are never touched."""
    if not image_url or UPLOAD_URL_PREFIX not in image_url:
        return
    name = image_url.rsplit("/", 1)[-1]
    (upload_root() / "parts" / name).unlink(missing_ok=True)
