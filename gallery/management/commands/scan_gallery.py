from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from gallery.scanner import scan_gallery


class Command(BaseCommand):
    help = 'Сканирует галерею'

    def add_arguments(self, parser):
        parser.add_argument(
            '--root',
            default=str(settings.MEDIA_ROOT / 'gallery'),
        )

    def handle(self, *args, **options):
        root = Path(options['root'])
        if not root.exists():
            self.stderr.write(f'Не найдено: {root}')
            return
        stats = scan_gallery(root, settings.MEDIA_ROOT)
        self.stdout.write(self.style.SUCCESS(
            f"Категорий: {stats['categories']}, "
            f"изображений: {stats['images']}, "
            f"ошибок: {len(stats['errors'])}"
        ))