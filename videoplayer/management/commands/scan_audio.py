from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from videoplayer.scanner import scan_audio


class Command(BaseCommand):
    help = 'Сканирует аудио-архив'

    def add_arguments(self, parser):
        parser.add_argument(
            '--root',
            default=str(settings.MEDIA_ROOT / 'audio'),
        )

    def handle(self, *args, **options):
        root = Path(options['root'])
        if not root.exists():
            self.stderr.write(f'Не найдено: {root}')
            return
        stats = scan_audio(root, settings.MEDIA_ROOT)
        self.stdout.write(self.style.SUCCESS(
            f"Каналов: {stats['channels']}, "
            f"плейлистов: {stats['playlists']}, "
            f"аудио: {stats['audios']}, "
            f"ошибок: {len(stats['errors'])}"
        ))