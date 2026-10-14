import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.db.models import Q

from videoplayer.models import Video
from videoplayer.media_tools import get_duration, generate_thumbnail


logger = logging.getLogger(__name__)


def _process_one(video_id: int, force: bool) -> tuple[int, bool, bool, str]:
    """
    В потоке: обновляет duration и thumbnail.
    Возвращает (video_id, duration_set, thumb_set, error).
    """
    close_old_connections()
    try:
        try:
            v = Video.objects.get(pk=video_id)
        except Video.DoesNotExist:
            logger.warning('video %s not found', video_id)
            return video_id, False, False, 'not found'

        full = Path(settings.MEDIA_ROOT) / v.file_path   # ← используем file_path
        if not full.exists():
            logger.warning('file missing: %s', full)
            return video_id, False, False, 'file missing'

        dur_set = False
        thumb_set = False
        err = ''

        if force or v.duration is None:
            d = get_duration(full)
            if d is not None:
                v.duration = d
                dur_set = True
            else:
                err = 'duration failed'
                logger.warning('duration failed: %s', v.file_path)

        if force or not v.thumbnail_path:
            rel = generate_thumbnail(full, v.file_path)
            if rel:
                v.thumbnail_path = rel
                thumb_set = True
            else:
                err = (err + '; thumb failed').strip('; ')
                logger.warning('thumbnail failed: %s', v.file_path)

        update_fields = []
        if dur_set:
            update_fields.append('duration')
        if thumb_set:
            update_fields.append('thumbnail_path')
        if update_fields:
            v.save(update_fields=update_fields)

        return video_id, dur_set, thumb_set, err
    finally:
        close_old_connections()


class Command(BaseCommand):
    help = 'Заполняет duration и thumbnail для видео (параллельно)'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перегенерить всё, даже если уже заполнено')
        parser.add_argument('--workers', type=int,
                            default=min(8, os.cpu_count() or 4))
        parser.add_argument('--limit', type=int, default=0)
        parser.add_argument('--verbose', action='store_true')

    def handle(self, *args, **opts):
        if opts['verbose']:
            logging.getLogger('videoplayer').setLevel(logging.DEBUG)

        force = opts['force']
        workers = opts['workers']
        limit = opts['limit']

        qs = Video.objects.all()
        if not force:
            qs = qs.filter(Q(duration__isnull=True) | Q(thumbnail_path=''))

        ids = list(qs.values_list('id', flat=True))
        if limit:
            ids = ids[:limit]

        total = len(ids)
        logger.info('enrich: total=%s workers=%s force=%s', total, workers, force)
        self.stdout.write(f'Обрабатываю: {total} видео в {workers} потоков')
        if total == 0:
            return

        done = dur_ok = thumb_ok = failed = 0

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_process_one, vid, force): vid for vid in ids}
            for fut in as_completed(futures):
                try:
                    vid, d_set, t_set, err = fut.result()
                except Exception:
                    logger.exception('worker crash for video %s', futures[fut])
                    failed += 1
                    done += 1
                    continue
                done += 1
                dur_ok += d_set
                thumb_ok += t_set
                if err:
                    failed += 1
                if done % 25 == 0 or done == total:
                    self.stdout.write(
                        f'  [{done}/{total}] duration+{dur_ok}, '
                        f'thumb+{thumb_ok}, failed={failed}'
                    )

        self.stdout.write(self.style.SUCCESS(
            f'\nГотово: {done} обработано, duration={dur_ok}, '
            f'thumbnail={thumb_ok}, ошибок={failed}'
        ))
        logger.info('enrich done: done=%s dur=%s thumb=%s fail=%s',
                    done, dur_ok, thumb_ok, failed)