import logging
from pathlib import Path

from django.db import transaction
from django.utils.text import slugify

from .models import Audio, Channel, Playlist, Video
from .parsing import parse_filename

logger = logging.getLogger(__name__)

VIDEO_EXTS = {'.mp4', '.mkv', '.webm', '.avi', '.mov'}
AUDIO_EXTS = {'.mp3', '.flac', '.m4a', '.aac', '.ogg', '.opus', '.wav'}
SKIP_DIR_PREFIX = '_'


def _scan_tree(root: Path, media_root: Path, upsert_file, stats: dict,
               exts: set[str]) -> dict:
    """Walk a directory tree, creating Channel/Playlist/Video-or-Audio records."""
    root = root.resolve()
    media_root = Path(media_root).resolve()

    with transaction.atomic():
        for channel_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            if channel_dir.name.startswith(SKIP_DIR_PREFIX):
                continue
            try:
                channel = _get_or_create_channel(channel_dir, media_root)
            except Exception as e:
                logger.exception('channel fail: %s', channel_dir)
                stats['errors'].append((str(channel_dir), str(e)))
                continue
            stats['channels'] += 1
            _walk(channel_dir, channel, None, media_root, stats, upsert_file, exts)

    return stats


def _walk(path, channel, parent_playlist, media_root, stats, upsert_file, exts):
    """Recursively walk a channel/playlist directory."""
    files = list(path.iterdir())
    target_files = [f for f in files
                    if f.is_file() and f.suffix.lower() in exts]
    dirs = [f for f in files
            if f.is_dir() and not f.name.startswith(SKIP_DIR_PREFIX)]

    for f in sorted(target_files):
        try:
            upsert_file(f, channel, parent_playlist, media_root, stats)
        except Exception as e:
            logger.exception('file fail: %s', f)
            stats['errors'].append((str(f), str(e)))

    for d in sorted(dirs):
        try:
            playlist = _get_or_create_playlist(d, channel, parent_playlist, media_root)
        except Exception as e:
            logger.exception('playlist fail: %s', d)
            stats['errors'].append((str(d), str(e)))
            continue
        stats['playlists'] += 1
        _walk(d, channel, playlist, media_root, stats, upsert_file, exts)


def _get_or_create_channel(path: Path, media_root: Path) -> Channel:
    name = path.name
    rel = str(path.relative_to(media_root))
    channel, created = Channel.objects.update_or_create(
        name=name,
        defaults={
            'slug': slugify(name) or f'channel-{abs(hash(name))}',
            'path': rel,
        },
    )
    logger.debug('channel %s: %s', 'created' if created else 'updated', name)
    return channel


def _get_or_create_playlist(path: Path, channel: Channel, parent,
                            media_root: Path) -> Playlist:
    rel = str(path.relative_to(media_root))
    playlist, created = Playlist.objects.update_or_create(
        channel=channel, parent=parent, name=path.name,
        defaults={'path': rel},
    )
    logger.debug('playlist %s: %s', 'created' if created else 'updated', path.name)
    return playlist


def _upsert_video(vf: Path, channel: Channel, playlist, media_root: Path,
                  stats: dict) -> None:
    """Create or update a Video record for a single file."""
    rel = str(vf.relative_to(media_root))
    recorded_at, title = parse_filename(vf.name)

    _, created = Video.objects.update_or_create(
        file_path=rel,
        defaults={
            'channel': channel,
            'playlist': playlist,
            'title': title,
            'recorded_at': recorded_at,
            'filename': vf.name,
            'size': vf.stat().st_size,
        },
    )
    stats['videos'] += 1
    logger.debug('video %s: %s', 'created' if created else 'updated', rel)


def _upsert_audio(af: Path, channel: Channel, playlist, media_root: Path,
                  stats: dict) -> None:
    """Create or update an Audio record for a single file."""
    rel = str(af.relative_to(media_root))
    recorded_at, title = parse_filename(af.name)

    Audio.objects.update_or_create(
        file_path=rel,
        defaults={
            'channel': channel,
            'playlist': playlist,
            'title': title,
            'recorded_at': recorded_at,
            'filename': af.name,
            'size': af.stat().st_size,
        },
    )
    stats['audios'] += 1
    logger.debug('audio: %s', rel)


def scan(root: Path, media_root: Path) -> dict:
    """Scan a video archive and return scan statistics."""
    logger.info('Scanning videos: root=%s', root)
    stats = {'channels': 0, 'playlists': 0, 'videos': 0, 'errors': []}
    _scan_tree(root, media_root, _upsert_video, stats, VIDEO_EXTS)
    logger.info('Videos done: %s', stats)
    return stats


def scan_audio(root: Path, media_root: Path) -> dict:
    """Scan an audio archive and return scan statistics."""
    logger.info('Scanning audio: root=%s', root)
    stats = {'channels': 0, 'playlists': 0, 'audios': 0, 'errors': []}
    _scan_tree(root, media_root, _upsert_audio, stats, AUDIO_EXTS)
    logger.info('Audio done: %s', stats)
    return stats