import logging
from pathlib import Path

from django.db import transaction
from django.utils.text import slugify

from .models import Channel, Document, Playlist
from .parsing import parse_filename

logger = logging.getLogger(__name__)

DOC_EXTS = {
    '.pdf', '.epub', '.fb2', '.djvu', '.mobi', '.azw3',
    '.doc', '.docx', '.odt', '.txt', '.md',
}
SKIP_DIR_PREFIX = '_'


def scan_documents(root: Path, media_root: Path) -> dict:
    root = root.resolve()
    media_root = Path(media_root).resolve()
    stats = {'channels': 0, 'playlists': 0, 'documents': 0, 'errors': []}

    logger.info('scan documents: %s', root)

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
            logger.info('channel: %s', channel.name)
            _walk(channel_dir, channel, None, media_root, stats)

    return stats


def _walk(path, channel, parent_playlist, media_root, stats):
    files = list(path.iterdir())
    doc_files = [f for f in files if f.is_file() and f.suffix.lower() in DOC_EXTS]
    dirs = [f for f in files if f.is_dir() and not f.name.startswith(SKIP_DIR_PREFIX)]

    for df in sorted(doc_files):
        try:
            _upsert_document(df, channel, parent_playlist, media_root, stats)
        except Exception as e:
            logger.exception('document fail: %s', df)
            stats['errors'].append((str(df), str(e)))

    for d in sorted(dirs):
        try:
            playlist = _get_or_create_playlist(d, channel, parent_playlist, media_root)
        except Exception as e:
            logger.exception('playlist fail: %s', d)
            stats['errors'].append((str(d), str(e)))
            continue
        stats['playlists'] += 1
        _walk(d, channel, playlist, media_root, stats)


def _get_or_create_channel(path, media_root):
    name = path.name
    rel = str(path.relative_to(media_root))
    channel, _ = Channel.objects.update_or_create(
        name=name,
        defaults={
            'slug': slugify(name) or f'channel-{abs(hash(name))}',
            'path': rel,
        },
    )
    return channel


def _get_or_create_playlist(path, channel, parent, media_root):
    rel = str(path.relative_to(media_root))
    playlist, _ = Playlist.objects.update_or_create(
        channel=channel, parent=parent, name=path.name,
        defaults={'path': rel},
    )
    return playlist


def _upsert_document(file, channel, playlist, media_root, stats):
    from .models import Category

    rel = str(file.relative_to(media_root))
    recorded_at, title = parse_filename(file.name)

    doc, _ = Document.objects.update_or_create(
        file_path=rel,
        defaults={
            'channel': channel,
            'playlist': playlist,
            'title': title,
            'recorded_at': recorded_at,
            'filename': file.name,
            'size': file.stat().st_size,
        },
    )

    # Категория = имя канала
    cat, _ = Category.objects.get_or_create(
        name=channel.name,
        defaults={'slug': slugify(channel.name) or f'cat-{channel.pk}'},
    )
    doc.categories.add(cat)

    stats['documents'] += 1