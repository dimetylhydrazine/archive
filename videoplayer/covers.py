import hashlib
import subprocess
from pathlib import Path

from django.conf import settings


COVERS_DIR_NAME = '_covers'
FFMPEG = 'ffmpeg'
FFPROBE = 'ffprobe'


def covers_dir() -> Path:
    d = Path(settings.MEDIA_ROOT) / 'videos' / COVERS_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def cover_rel_path(video_rel_path: str) -> str:
    h = hashlib.sha1(video_rel_path.encode('utf-8')).hexdigest()
    return f'videos/{COVERS_DIR_NAME}/{h}.jpg'


def has_embedded_cover(video: Path) -> bool:
    """Есть ли в mp4 встроенная обложка (attached_pic)."""
    try:
        out = subprocess.run(
            [FFPROBE, '-v', 'error', '-select_streams', 'v',
             '-show_entries', 'stream=disposition',
             '-of', 'default=noprint_wrappers=1', str(video)],
            capture_output=True, text=True, timeout=10,
        )
        return 'attached_pic=1' in out.stdout
    except Exception:
        return False


def extract_cover(video: Path, dest: Path, at_sec: int = 10) -> bool:
    """
    Извлекает обложку из video в dest (.jpg).
    Сначала пробует встроенную, потом кадр на at_sec.
    Возвращает True при успехе.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.tmp.jpg')

    # 1) Попытка вытащить встроенную обложку
    if has_embedded_cover(video):
        cmd = [
            FFMPEG, '-y', '-i', str(video),
            '-map', '0:v', '-map', '-0:V',
            '-c', 'copy', str(tmp),
        ]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 0:
            tmp.rename(dest)
            return True

    # 2) Fallback — кадр на at_sec
    cmd = [
        FFMPEG, '-y',
        '-ss', str(at_sec),
        '-i', str(video),
        '-frames:v', '1',
        '-q:v', '2',
        str(tmp),
    ]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 0:
        tmp.rename(dest)
        return True

    # не получилось — подчищаем
    if tmp.exists():
        tmp.unlink()
    return False


def ensure_cover(video_abs: Path, video_rel_path: str, force: bool = False) -> str:
    """
    Гарантирует наличие превью в _covers. Возвращает относительный путь от MEDIA_ROOT
    или '' при неудаче.
    """
    rel = cover_rel_path(video_rel_path)
    dest = Path(settings.MEDIA_ROOT) / rel

    if dest.exists() and not force:
        return rel

    ok = extract_cover(video_abs, dest)
    return rel if ok else ''

import hashlib


COVERS_DIR_NAME = '_covers'


def cover_rel_path(source_rel_path: str, ext: str = '.jpg') -> str:
    """
    Относительный путь обложки от MEDIA_ROOT.
    Хэш от rel-пути источника — стабильно и уникально.
    """
    h = hashlib.sha1(source_rel_path.encode('utf-8')).hexdigest()
    return f'videos/{COVERS_DIR_NAME}/{h}{ext.lower()}'