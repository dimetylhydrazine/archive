import json
import logging
import subprocess
from pathlib import Path

from django.conf import settings

from .covers import cover_rel_path


logger = logging.getLogger(__name__)

FFMPEG = 'ffmpeg'
FFPROBE = 'ffprobe'
DEFAULT_TIMEOUT = 15


# ---------- Общие утилиты ----------

def _run_ffmpeg(cmd: list[str], out: Path, timeout: int) -> bool:
    """Запускает ffmpeg, возвращает True, если файл создан и непустой."""
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.warning('ffmpeg timeout: %s', out.name)
        return False
    except FileNotFoundError:
        logger.error('ffmpeg не найден. Установи ffmpeg.')
        raise

    if r.returncode != 0:
        logger.debug('ffmpeg rc=%s: %s', r.returncode, r.stderr[-300:])
        return False
    return out.exists() and out.stat().st_size > 0


def _save_cover_bytes(data: bytes, audio_rel_path: str, ext: str) -> str:
    """Сохраняет байты в _covers, возвращает rel-путь или ''."""
    rel = cover_rel_path(audio_rel_path, ext=ext)
    dest = Path(settings.MEDIA_ROOT) / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        dest.write_bytes(data)
    except Exception as e:
        logger.warning('cover write fail: %s: %s', audio_rel_path, e)
        return ''
    return rel


def _cover_already_exists(audio_rel_path: str, ext: str = '.jpg') -> tuple[bool, str]:
    """Проверяет, есть ли уже обложка. Возвращает (exists, rel_path)."""
    rel = cover_rel_path(audio_rel_path, ext=ext)
    dest = Path(settings.MEDIA_ROOT) / rel
    if dest.exists() and dest.stat().st_size > 0:
        return True, rel
    return False, rel


# ---------- Видео: длительность и обложка ----------

def get_duration(video_path: Path, timeout: int = DEFAULT_TIMEOUT) -> int | None:
    """Длительность видео через ffprobe."""
    return _ffprobe_duration(video_path, timeout)


def _ffprobe_duration(path: Path, timeout: int) -> int | None:
    cmd = [
        FFPROBE, '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(path),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        logger.error('ffprobe не найден')
        raise
    if r.returncode != 0:
        return None
    try:
        return int(float(r.stdout.strip()))
    except (ValueError, TypeError):
        return None


def has_embedded_cover(video_path: Path, timeout: int = 10) -> bool:
    """True, если в файле есть mjpeg/png поток-обложка."""
    cmd = [
        FFPROBE, '-v', 'error',
        '-select_streams', 'v',
        '-show_entries', 'stream=index,codec_name',
        '-of', 'json',
        str(video_path),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False
    if r.returncode != 0:
        return False
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return False
    return any(s.get('codec_name') in ('mjpeg', 'png')
               for s in data.get('streams', []))


def generate_thumbnail(video_path: Path, video_rel_path: str,
                       at_sec: int = 1, timeout: int = 30) -> str:
    """
    Обложка для видео: встроенная → первый кадр → кадр на at_sec.
    Возвращает rel-путь или ''.
    """
    exists, rel = _cover_already_exists(video_rel_path)
    if exists:
        return rel

    dest = Path(settings.MEDIA_ROOT) / rel
    tmp = dest.with_suffix('.tmp.jpg')

    # 1) встроенная обложка
    if has_embedded_cover(video_path):
        cmd = [
            FFMPEG, '-y', '-i', str(video_path),
            '-map', '0:v', '-map', '-0:V',
            '-c', 'copy', '-frames:v', '1',
            '-f', 'image2', str(tmp),
        ]
        if _run_ffmpeg(cmd, tmp, timeout):
            tmp.rename(dest)
            return rel

    # 2) первый кадр
    cmd = [
        FFMPEG, '-y', '-i', str(video_path),
        '-frames:v', '1', '-q:v', '2', str(tmp),
    ]
    if _run_ffmpeg(cmd, tmp, timeout):
        tmp.rename(dest)
        return rel

    # 3) кадр на at_sec
    cmd = [
        FFMPEG, '-y', '-ss', str(at_sec), '-i', str(video_path),
        '-frames:v', '1', '-q:v', '2', str(tmp),
    ]
    if _run_ffmpeg(cmd, tmp, timeout):
        tmp.rename(dest)
        return rel

    if tmp.exists():
        tmp.unlink()
    return ''


# ---------- Аудио: длительность и обложка ----------

def get_audio_duration(audio_path: Path, timeout: int = DEFAULT_TIMEOUT) -> int | None:
    """Длительность: MP3 через mutagen, остальное — ffprobe."""
    if audio_path.suffix.lower() == '.mp3':
        d = _mp3_duration(audio_path)
        if d is not None:
            return d
    return _ffprobe_duration(audio_path, timeout)


def _mp3_duration(path: Path) -> int | None:
    try:
        from mutagen.mp3 import MP3
        audio = MP3(str(path))
        if audio.info and audio.info.length:
            return int(audio.info.length)
    except Exception as e:
        logger.debug('mp3 duration fail: %s: %s', path, e)
    return None


def extract_audio_cover(audio_path: Path, audio_rel_path: str,
                        timeout: int = DEFAULT_TIMEOUT) -> str:
    """Обложка: MP3 → mutagen, остальное → ffmpeg."""
    if audio_path.suffix.lower() == '.mp3':
        rel = _extract_mp3_cover(audio_path, audio_rel_path)
        if rel:
            return rel
    return _extract_audio_cover_ffmpeg(audio_path, audio_rel_path, timeout)


def _extract_mp3_cover(audio_path: Path, audio_rel_path: str) -> str:
    from mutagen.id3 import ID3, ID3NoHeaderError

    exists, rel = _cover_already_exists(audio_rel_path)
    if exists:
        return rel

    try:
        tags = ID3(str(audio_path))
    except ID3NoHeaderError:
        return ''
    except Exception as e:
        logger.warning('mp3 mutagen fail: %s: %s', audio_rel_path, e)
        return ''

    apic = None
    for frame in tags.values():
        if frame.FrameID in ('APIC', 'PIC'):
            apic = frame
            if getattr(frame, 'type', None) == 3:
                break

    if apic is None or not apic.data:
        return ''

    mime = (getattr(apic, 'mime', '') or '').lower()
    ext = '.png' if 'png' in mime else '.jpg'
    return _save_cover_bytes(apic.data, audio_rel_path, ext)


def _extract_audio_cover_ffmpeg(audio_path: Path, audio_rel_path: str,
                                 timeout: int) -> str:
    exists, rel = _cover_already_exists(audio_rel_path)
    if exists:
        return rel

    dest = Path(settings.MEDIA_ROOT) / rel
    tmp = dest.with_suffix('.tmp.jpg')

    cmd = [
        FFMPEG, '-y', '-i', str(audio_path),
        '-an', '-c:v', 'copy', '-frames:v', '1',
        '-f', 'image2', str(tmp),
    ]
    if _run_ffmpeg(cmd, tmp, timeout):
        tmp.rename(dest)
        return rel

    if tmp.exists():
        tmp.unlink()
    return ''