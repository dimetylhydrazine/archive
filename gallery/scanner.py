import logging
from pathlib import Path

from django.db import transaction
from django.utils.text import slugify

from .models import Category, Image
from .parsing import parse_filename

logger = logging.getLogger(__name__)

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff', '.heic', '.avif'}
SKIP_DIR_PREFIX = '_'


def scan_gallery(root: Path, media_root: Path) -> dict:
    root = root.resolve()
    media_root = Path(media_root).resolve()
    stats = {'categories': 0, 'images': 0, 'errors': []}

    logger.info('Сканирование галереи: %s', root)

    with transaction.atomic():
        for category_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            if category_dir.name.startswith(SKIP_DIR_PREFIX):
                continue
            try:
                category = _get_or_create_category(category_dir)
            except Exception as e:
                logger.exception('category fail: %s', category_dir)
                stats['errors'].append((str(category_dir), str(e)))
                continue
            stats['categories'] += 1
            logger.info('category: %s', category.name)

            # все картинки рекурсивно внутри категории
            for img_file in category_dir.rglob('*'):
                if not img_file.is_file():
                    continue
                if img_file.suffix.lower() not in IMAGE_EXTS:
                    continue
                try:
                    _upsert_image(img_file, category, media_root, stats)
                except Exception as e:
                    logger.exception('image fail: %s', img_file)
                    stats['errors'].append((str(img_file), str(e)))

    logger.info('Готово: %s', stats)
    return stats


def _get_or_create_category(path: Path) -> Category:
    name = path.name
    category, _ = Category.objects.update_or_create(
        name=name,
        defaults={'slug': slugify(name) or f'cat-{abs(hash(name))}'},
    )
    return category


def _upsert_image(file: Path, category: Category, media_root: Path, stats: dict):
    rel = str(file.relative_to(media_root))
    recorded_at, title = parse_filename(file.name)

    img, _ = Image.objects.update_or_create(
        file_path=rel,
        defaults={
            'title': title,
            'recorded_at': recorded_at,
            'filename': file.name,
            'size': file.stat().st_size,
        },
    )
    img.categories.add(category)
    stats['images'] += 1