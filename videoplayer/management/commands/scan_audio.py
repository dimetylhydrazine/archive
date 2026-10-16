from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from videoplayer.scanner import scan_audio


class Command(BaseCommand):
    help = 'Scan the audio archive'

    def add_arguments(self, parser):
        parser.add_argument(
            '--root',
            default=str(settings.MEDIA_ROOT / 'audio'),
            help='Root directory of the audio archive',
        )

    def handle(self, *args, **options):
        root = Path(options['root'])
        if not root.exists():
            self.stderr.write(self.style.ERROR(f'Not found: {root}'))
            return

        stats = scan_audio(root, settings.MEDIA_ROOT)

        self.stdout.write(self.style.SUCCESS(
            f"Channels: {stats['channels']}, "
            f"playlists: {stats['playlists']}, "
            f"audio: {stats['audios']}, "
            f"errors: {len(stats['errors'])}"
        ))