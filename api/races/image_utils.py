import os
import uuid
from pathlib import Path

from django.conf import settings
from PIL import Image

THUMB_WIDTH = 600
WEBP_QUALITY = 82

try:
    RESAMPLE_FILTER = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE_FILTER = Image.LANCZOS


def save_upload(uploaded_file, subdir='races'):
    """Save an uploaded file under MEDIA_ROOT/<subdir>/ and return its relative path."""
    ext = os.path.splitext(uploaded_file.name)[1].lower() or '.bin'
    filename = f'{uuid.uuid4().hex}{ext}'
    rel_path = f'{subdir}/{filename}'
    abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, 'wb+') as dest:
        for chunk in uploaded_file.chunks():
            dest.write(chunk)
    return rel_path


def delete_upload(rel_path):
    """Delete the uploaded original and its derived WebP/thumb files (best-effort)."""
    if not rel_path:
        return
    src = Path(settings.MEDIA_ROOT) / rel_path
    stem = src.stem
    parent = src.parent
    for target in (src, parent / f'{stem}.webp', parent / 'thumbs' / f'{stem}.webp'):
        try:
            target.unlink()
        except (OSError, FileNotFoundError):
            pass


def process_image(rel_path):
    """Convert image to WebP and create thumbnail.

    Args:
        rel_path: Relative path from MEDIA_ROOT (e.g., 'races/123.png')

    Returns:
        dict with 'webp' and 'thumb' relative paths, or None on failure.
    """
    src = Path(settings.MEDIA_ROOT) / rel_path
    if not src.exists():
        return None

    stem = src.stem
    parent = src.parent

    # WebP full-size
    webp_path = parent / f'{stem}.webp'
    # Thumbnail in thumbs/ subdirectory
    thumb_dir = parent / 'thumbs'
    thumb_path = thumb_dir / f'{stem}.webp'

    try:
        with Image.open(src) as img:
            img = img.convert('RGBA') if img.mode == 'RGBA' else img.convert('RGB')

            # Save WebP full-size
            img.save(str(webp_path), 'WEBP', quality=WEBP_QUALITY)

            # Save thumbnail
            thumb_dir.mkdir(parents=True, exist_ok=True)
            thumb = img.copy()
            if thumb.width > THUMB_WIDTH:
                ratio = THUMB_WIDTH / thumb.width
                new_height = int(thumb.height * ratio)
                thumb = thumb.resize((THUMB_WIDTH, new_height), Image.LANCZOS)
            thumb.save(str(thumb_path), 'WEBP', quality=WEBP_QUALITY)

    except Exception:
        return None

    # Return relative paths from MEDIA_ROOT
    rel_parent = Path(rel_path).parent
    return {
        'webp': str(rel_parent / f'{stem}.webp'),
        'thumb': str(rel_parent / 'thumbs' / f'{stem}.webp'),
    }


def get_webp_path(rel_path):
    """Return WebP relative path if file exists, else original."""
    if not rel_path:
        return rel_path
    stem = Path(rel_path).stem
    parent = Path(rel_path).parent
    webp_rel = str(parent / f'{stem}.webp')
    webp_abs = Path(settings.MEDIA_ROOT) / webp_rel
    if webp_abs.exists():
        return webp_rel
    return rel_path


def get_thumb_path(rel_path):
    """Return thumbnail relative path if file exists, else None."""
    if not rel_path:
        return None
    stem = Path(rel_path).stem
    parent = Path(rel_path).parent
    thumb_rel = str(parent / 'thumbs' / f'{stem}.webp')
    thumb_abs = Path(settings.MEDIA_ROOT) / thumb_rel
    if thumb_abs.exists():
        return thumb_rel
    return None
