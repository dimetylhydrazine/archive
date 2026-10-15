import hashlib
import logging
import subprocess
from pathlib import Path

from django.conf import settings


logger = logging.getLogger(__name__)

COVERS_DIR_NAME = '_covers'
DEFAULT_TIMEOUT = 30


def cover_rel_path(source_rel_path: str, ext: str = '.jpg') -> str:
    h = hashlib.sha1(source_rel_path.encode('utf-8')).hexdigest()
    return f'documents/{COVERS_DIR_NAME}/{h}{ext.lower()}'


def get_page_count(doc_path: Path, timeout: int = DEFAULT_TIMEOUT) -> int | None:
    """Число страниц PDF через pdfinfo."""
    if doc_path.suffix.lower() != '.pdf':
        return None
    cmd = ['pdfinfo', str(doc_path)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if r.returncode != 0:
        return None
    for line in r.stdout.splitlines():
        if line.startswith('Pages:'):
            try:
                return int(line.split(':')[1].strip())
            except (ValueError, IndexError):
                return None
    return None


def generate_cover_pdf(doc_path: Path, doc_rel_path: str,
                       timeout: int = DEFAULT_TIMEOUT) -> str:
    """Превью первой страницы PDF через pdftoppm."""
    rel = cover_rel_path(doc_rel_path, ext='.jpg')
    dest = Path(settings.MEDIA_ROOT) / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return rel

    # pdftoppm создаёт файл с суффиксом -1, -01, и т.п.
    prefix = dest.with_suffix('')   # убираем .jpg
    tmp_prefix = str(prefix) + '.tmp'

    cmd = [
        'pdftoppm',
        '-jpeg',
        '-f', '1', '-l', '1',
        '-scale-to', '600',
        str(doc_path),
        tmp_prefix,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.warning('pdftoppm timeout: %s', doc_rel_path)
        return ''
    except FileNotFoundError:
        logger.error('pdftoppm не найден. Установи poppler-utils.')
        raise

    if r.returncode != 0:
        logger.warning('pdftoppm rc=%s: %s', r.returncode, doc_rel_path)
        return ''

    # Ищем созданный файл: tmp_prefix-1.jpg, tmp_prefix-01.jpg
    parent = dest.parent
    candidates = sorted(parent.glob(f'{Path(tmp_prefix).name}-*.jpg'))
    if not candidates:
        return ''

    candidates[0].rename(dest)
    # Чистим остальные
    for c in candidates[1:]:
        c.unlink()

    return rel


def generate_cover_mupdf(doc_path: Path, doc_rel_path: str) -> str:
    """Превью через PyMuPDF для epub/fb2/mobi и любых других."""
    rel = cover_rel_path(doc_rel_path, ext='.jpg')
    dest = Path(settings.MEDIA_ROOT) / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return rel

    try:
        import fitz   # PyMuPDF
    except ImportError:
        logger.warning('PyMuPDF не установлен')
        return ''

    try:
        doc = fitz.open(str(doc_path))
    except Exception as e:
        logger.warning('PyMuPDF open fail: %s: %s', doc_rel_path, e)
        return ''

    try:
        if doc.page_count == 0:
            return ''
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        pix.save(str(dest))
        return rel
    except Exception as e:
        logger.warning('PyMuPDF render fail: %s: %s', doc_rel_path, e)
        return ''
    finally:
        doc.close()


def generate_cover(doc_path: Path, doc_rel_path: str) -> str:
    """Универсальная точка входа."""
    ext = doc_path.suffix.lower()
    if ext == '.pdf':
        rel = generate_cover_pdf(doc_path, doc_rel_path)
        if rel:
            return rel
    return generate_cover_mupdf(doc_path, doc_rel_path)