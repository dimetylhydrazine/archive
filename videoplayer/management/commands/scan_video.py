import logging
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from videoplayer.scanner import scan

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scan the video archive and update the DB tree'

    def add_arguments(self, parser):
        parser.add_argument(
            '--root',
            default=str(settings.MEDIA_ROOT / 'videos'),
            help='Root directory of the video archive',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable debug logging',
        )

    def handle(self, *args, **options):
        if options['verbose']:
            logging.getLogger('videoplayer').setLevel(logging.DEBUG)

        root = Path(options['root'])
        if not root.exists():
            self.stderr.write(self.style.ERROR(f'Not found: {root}'))
            logger.error('root does not exist: %s', root)
            return

        try:
            stats = scan(root, settings.MEDIA_ROOT)
        except KeyboardInterrupt:
            self.stderr.write(self.style.WARNING('\nInterrupted by user'))
            logger.warning('scan_archive interrupted')
            return

        self.stdout.write(self.style.SUCCESS(
            f"Channels: {stats['channels']}\n"
            f"Playlists: {stats['playlists']}\n"
            f"Videos: {stats['videos']}\n"
            f"Errors: {len(stats['errors'])}"
        ))

        for path, err in stats['errors'][:20]:
            self.stdout.write(self.style.WARNING(f'  {path}: {err}'))