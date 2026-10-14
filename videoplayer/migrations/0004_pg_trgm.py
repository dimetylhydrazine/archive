from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('videoplayer', '0003_audio'),
    ]

    operations = [
        TrigramExtension(),
    ]