from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from documents.scanner import scan_documents
from gallery.scanner import scan_gallery
from videoplayer.scanner import scan, scan_audio


class Command(BaseCommand):
    help = 'Сканирует все типы медиа'

    def handle(self, *args, **options):
        media = Path(settings.MEDIA_ROOT)

        if (media / 'videos').exists():
            stats = scan(media / 'videos', media)
            self.stdout.write(f"[video] каналов={stats['channels']}, "
                              f"плейлистов={stats['playlists']}, "
                              f"видео={stats['videos']}")

        if (media / 'audio').exists():
            stats = scan_audio(media / 'audio', media)
            self.stdout.write(f"[audio] каналов={stats['channels']}, "
                              f"плейлистов={stats['playlists']}, "
                              f"аудио={stats['audios']}")

        if (media / 'pdf').exists() or (media / 'documents').exists():
            root = media / 'pdf' if (media / 'pdf').exists() else media / 'documents'
            stats = scan_documents(root, media)
            self.stdout.write(f"[documents] каналов={stats['channels']}, "
                              f"плейлистов={stats['playlists']}, "
                              f"документов={stats['documents']}")

        if (media / 'gallery').exists():
            stats = scan_gallery(media / 'gallery', media)
            self.stdout.write(f"[gallery] категорий={stats['categories']}, "
                              f"изображений={stats['images']}")

        self.stdout.write(self.style.SUCCESS('Готово'))