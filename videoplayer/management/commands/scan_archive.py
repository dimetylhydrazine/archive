import logging
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from videoplayer.scanner import scan


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Сканирует архив видео и обновляет дерево в БД (без ffmpeg)'

    def add_arguments(self, parser):
        parser.add_argument('--root', default=str(settings.MEDIA_ROOT / 'videos'))
        parser.add_argument('--verbose', action='store_true')

    def handle(self, *args, **options):
        if options['verbose']:
            logging.getLogger('videoplayer').setLevel(logging.DEBUG)

        root = Path(options['root'])
        if not root.exists():
            self.stderr.write(self.style.ERROR(f'Не найдено: {root}'))
            logger.error('root не существует: %s', root)
            return

        try:
            stats = scan(root, settings.MEDIA_ROOT)
        except KeyboardInterrupt:
            self.stderr.write(self.style.WARNING('\nПрервано пользователем'))
            logger.warning('scan_archive прерван')
            return

        self.stdout.write(self.style.SUCCESS(
            f"Каналов: {stats['channels']}\n"
            f"Плейлистов: {stats['playlists']}\n"
            f"Видео: {stats['videos']}\n"
            f"Ошибок: {len(stats['errors'])}"
        ))
        for path, err in stats['errors'][:20]:
            self.stdout.write(self.style.WARNING(f'  {path}: {err}'))