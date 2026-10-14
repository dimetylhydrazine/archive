from django.contrib.postgres.indexes import GinIndex
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('videoplayer', '0004_pg_trgm'),
    ]

    operations = [
        # GIN для trigram по title
        migrations.AddIndex(
            model_name='video',
            index=GinIndex(
                fields=['title'],
                name='video_title_trgm',
                opclasses=['gin_trgm_ops'],
            ),
        ),
        migrations.AddIndex(
            model_name='audio',
            index=GinIndex(
                fields=['title'],
                name='audio_title_trgm',
                opclasses=['gin_trgm_ops'],
            ),
        ),
    ]