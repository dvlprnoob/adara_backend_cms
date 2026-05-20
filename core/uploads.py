from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile


UPLOAD_ROOT = Path(__file__).resolve().parent.parent / "uploads"
MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg": ".jpg",
    ".jpeg": ".jpg",
    ".png": ".png",
    ".webp": ".webp",
}


async def save_upload_image(file: UploadFile, folder: str) -> str:
    extension = ALLOWED_IMAGE_TYPES.get(file.content_type)

    if extension is None and file.filename:
        suffix = Path(file.filename).suffix.lower()
        extension = ALLOWED_IMAGE_EXTENSIONS.get(suffix)

    contents = await file.read()

    if extension is None:
        extension = detect_image_extension(contents)

    if extension is None:
        content_type = file.content_type or "unknown"
        filename = file.filename or "unknown"
        raise HTTPException(
            status_code=400,
            detail=f"Only JPG, JPEG, PNG, or WEBP images are allowed. Received {filename} ({content_type})"
        )

    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="Image size must be 5MB or less")

    upload_dir = UPLOAD_ROOT / folder
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}{extension}"
    file_path = upload_dir / filename
    file_path.write_bytes(contents)

    return f"/uploads/{folder}/{filename}"


def detect_image_extension(contents: bytes) -> str | None:
    if contents.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if contents.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if contents.startswith(b"RIFF") and contents[8:12] == b"WEBP":
        return ".webp"
    return None
