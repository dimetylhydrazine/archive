import hashlib
import logging
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

THUMB_DIR_NAME = '_thumbs'
THUMB_SIZE = (400, 400)   # max width/height
THUMB_QUALITY = 82


def thumb_rel_path(source_rel_path: str, ext: str = '.webp') -> str:
    h = hashlib.sha1(source_rel_path.encode('utf-8')).hexdigest()
    return f'gallery/{THUMB_DIR_NAME}/{h[:2]}/{h}{ext}'


def generate_thumb(img_path: Path, img_rel_path: str) -> str:
    """Миниатюра через Pillow. Возвращает rel-путь или ''."""
    try:
        from PIL import Image as PILImage
        from PIL import ImageOps
    except ImportError:
        logger.error('Pillow не установлен')
        return ''

    rel = thumb_rel_path(img_rel_path, ext='.webp')
    dest = Path(settings.MEDIA_ROOT) / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return rel

    try:
        img = PILImage.open(img_path)
        img = ImageOps.exif_transpose(img)   # поворот по EXIF
        img.thumbnail(THUMB_SIZE, PILImage.LANCZOS)

        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        img.save(dest, 'WEBP', quality=THUMB_QUALITY, method=6)
    except Exception as e:
        logger.warning('thumb fail: %s: %s', img_rel_path, e)
        return ''

    return rel


def get_dimensions(img_path: Path) -> tuple[int, int] | None:
    """Возвращает (width, height) или None."""
    try:
        from PIL import Image as PILImage
        img = PILImage.open(img_path)
        return img.size
    except Exception:
        return None