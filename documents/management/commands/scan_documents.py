from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from documents.scanner import scan_documents


class Command(BaseCommand):
    help = 'Сканирует архив документов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--root',
            default=str(settings.MEDIA_ROOT / 'pdf'),
        )

    def handle(self, *args, **options):
        root = Path(options['root'])
        if not root.exists():
            self.stderr.write(f'Не найдено: {root}')
            return
        stats = scan_documents(root, settings.MEDIA_ROOT)
        self.stdout.write(self.style.SUCCESS(
            f"Каналов: {stats['channels']}, "
            f"плейлистов: {stats['playlists']}, "
            f"документов: {stats['documents']}, "
            f"ошибок: {len(stats['errors'])}"
        ))