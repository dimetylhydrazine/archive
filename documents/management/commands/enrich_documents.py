import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.db.models import Q

from documents.models import Document
from documents.media_tools import generate_cover, get_page_count


logger = logging.getLogger(__name__)


def _process_one(doc_id: int, force: bool):
    close_old_connections()
    try:
        try:
            d = Document.objects.get(pk=doc_id)
        except Document.DoesNotExist:
            return doc_id, False, False, 'not found'

        full = Path(settings.MEDIA_ROOT) / d.file_path
        if not full.exists():
            return doc_id, False, False, 'file missing'

        cover_set = False
        pages_set = False
        err = ''

        if force or not d.cover_path:
            rel = generate_cover(full, d.file_path)
            if rel:
                d.cover_path = rel
                cover_set = True

        if force or d.pages is None:
            p = get_page_count(full)
            if p is not None:
                d.pages = p
                pages_set = True

        update_fields = []
        if cover_set: update_fields.append('cover_path')
        if pages_set: update_fields.append('pages')
        if not cover_set and not pages_set:
            d.enrich_failed = True
            update_fields.append('enrich_failed')

        if update_fields:
            d.save(update_fields=update_fields)

        return doc_id, pages_set, cover_set, err
    finally:
        close_old_connections()


class Command(BaseCommand):
    help = 'Заполняет превью и число страниц для документов'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--workers', type=int,
                            default=min(2, os.cpu_count() or 1))
        parser.add_argument('--limit', type=int, default=0)

    def handle(self, *args, **opts):
        force = opts['force']
        workers = opts['workers']
        limit = opts['limit']

        qs = Document.objects.filter(enrich_failed=False)
        if not force:
            qs = qs.filter(Q(cover_path='') | Q(pages__isnull=True))

        ids = list(qs.values_list('id', flat=True))
        if limit:
            ids = ids[:limit]

        total = len(ids)
        self.stdout.write(f'[{total}] документов, {workers} потоков')
        if total == 0:
            return

        done = cover_ok = pages_ok = failed = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_process_one, did, force): did for did in ids}
            for fut in as_completed(futures):
                try:
                    did, p_set, c_set, err = fut.result()
                except Exception:
                    logger.exception('worker crash %s', futures[fut])
                    failed += 1; done += 1
                    continue
                done += 1
                cover_ok += c_set
                pages_ok += p_set
                if err:
                    failed += 1
                if done % 25 == 0 or done == total:
                    self.stdout.write(
                        f'  [{done}/{total}] cover+{cover_ok}, pages+{pages_ok}, failed={failed}'
                    )

        self.stdout.write(self.style.SUCCESS(
            f'Готово: {done}, cover={cover_ok}, pages={pages_ok}, failed={failed}'
        ))