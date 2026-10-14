import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.db.models import Q

from videoplayer.models import Audio
from videoplayer.media_tools import get_audio_duration, extract_audio_cover


logger = logging.getLogger(__name__)


def _process_one(audio_id: int, force: bool):
    close_old_connections()
    try:
        try:
            a = Audio.objects.get(pk=audio_id)
        except Audio.DoesNotExist:
            return audio_id, False, False, 'not found'

        full = Path(settings.MEDIA_ROOT) / a.file_path
        if not full.exists():
            return audio_id, False, False, 'file missing'

        dur_set = False
        cover_set = False
        err = ''

        if force or a.duration is None:
            d = get_audio_duration(full)
            if d is not None:
                a.duration = d
                dur_set = True

        if force or not a.cover_path:
            rel = extract_audio_cover(full, a.file_path)
            if rel:
                a.cover_path = rel
                cover_set = True
            else:
                err = 'cover failed'

        update_fields = []
        if dur_set: update_fields.append('duration')
        if cover_set: update_fields.append('cover_path')
        if update_fields:
            a.save(update_fields=update_fields)

        return audio_id, dur_set, cover_set, err
    finally:
        close_old_connections()


class Command(BaseCommand):
    help = 'Заполняет duration и cover для аудио'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--workers', type=int,
                            default=min(8, os.cpu_count() or 4))
        parser.add_argument('--limit', type=int, default=0)

    def handle(self, *args, **opts):
        force = opts['force']
        workers = opts['workers']
        limit = opts['limit']

        qs = Audio.objects.all()
        if not force:
            qs = qs.filter(Q(duration__isnull=True) | Q(cover_path=''))

        ids = list(qs.values_list('id', flat=True))
        if limit:
            ids = ids[:limit]

        total = len(ids)
        self.stdout.write(f'Обрабатываю: {total} аудио в {workers} потоков')
        if total == 0:
            return

        done = dur_ok = cover_ok = failed = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_process_one, aid, force): aid for aid in ids}
            for fut in as_completed(futures):
                try:
                    aid, d_set, c_set, err = fut.result()
                except Exception:
                    logger.exception('audio worker crash %s', futures[fut])
                    failed += 1
                    done += 1
                    continue
                done += 1
                dur_ok += d_set
                cover_ok += c_set
                if err:
                    failed += 1
                if done % 25 == 0 or done == total:
                    self.stdout.write(
                        f'  [{done}/{total}] duration+{dur_ok}, '
                        f'cover+{cover_ok}, failed={failed}'
                    )

        self.stdout.write(self.style.SUCCESS(
            f'\nГотово: {done}, duration={dur_ok}, cover={cover_ok}, failed={failed}'
        ))