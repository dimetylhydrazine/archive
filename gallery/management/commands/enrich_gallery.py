import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.db.models import Q

from gallery.media_tools import generate_thumb, get_dimensions
from gallery.models import Image

logger = logging.getLogger(__name__)


def _process_one(img_id: int, force: bool):
    close_old_connections()
    try:
        try:
            img = Image.objects.get(pk=img_id)
        except Image.DoesNotExist:
            return img_id, False, False, 'not found'

        full = Path(settings.MEDIA_ROOT) / img.file_path
        if not full.exists():
            return img_id, False, False, 'file missing'

        thumb_set = False
        dim_set = False

        if force or not img.thumb_path:
            rel = generate_thumb(full, img.file_path)
            if rel:
                img.thumb_path = rel
                thumb_set = True

        if force or img.width is None or img.height is None:
            dims = get_dimensions(full)
            if dims:
                img.width, img.height = dims
                dim_set = True

        update_fields = []
        if thumb_set: update_fields.append('thumb_path')
        if dim_set: update_fields.extend(['width', 'height'])
        if not thumb_set and not dim_set:
            img.enrich_failed = True
            update_fields.append('enrich_failed')

        if update_fields:
            img.save(update_fields=update_fields)

        return img_id, dim_set, thumb_set, ''
    finally:
        close_old_connections()


class Command(BaseCommand):
    help = 'Генерирует миниатюры и размеры для картинок'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--workers', type=int,
                            default=min(4, os.cpu_count() or 2))
        parser.add_argument('--limit', type=int, default=0)

    def handle(self, *args, **opts):
        force = opts['force']
        workers = opts['workers']
        limit = opts['limit']

        qs = Image.objects.filter(enrich_failed=False)
        if not force:
            qs = qs.filter(Q(thumb_path='') | Q(width__isnull=True))

        ids = list(qs.values_list('id', flat=True))
        if limit:
            ids = ids[:limit]

        total = len(ids)
        self.stdout.write(f'[{total}] картинок, {workers} потоков')
        if total == 0:
            return

        done = thumb_ok = dim_ok = failed = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_process_one, iid, force): iid for iid in ids}
            for fut in as_completed(futures):
                try:
                    iid, d_set, t_set, err = fut.result()
                except Exception:
                    logger.exception('worker crash %s', futures[fut])
                    failed += 1; done += 1
                    continue
                done += 1
                thumb_ok += t_set
                dim_ok += d_set
                if err:
                    failed += 1
                if done % 50 == 0 or done == total:
                    self.stdout.write(
                        f'  [{done}/{total}] thumb+{thumb_ok}, dims+{dim_ok}, failed={failed}'
                    )

        self.stdout.write(self.style.SUCCESS(
            f'Готово: {done}, thumb={thumb_ok}, dims={dim_ok}, failed={failed}'
        ))