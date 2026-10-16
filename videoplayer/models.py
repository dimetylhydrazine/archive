# archive/models.py
from django.contrib.postgres.indexes import GinIndex
from django.db import models


class Channel(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    path = models.CharField(max_length=1024)   # относительный путь от MEDIA_ROOT
    is_visible = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Playlist(models.Model):
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name='playlists'
    )
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True, related_name='children'
    )
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=1024)   # относительный путь

    class Meta:
        ordering = ['name']
        unique_together = [('channel', 'parent', 'name')]

    def __str__(self):
        return self.name

    @property
    def is_root(self):
        return self.parent is None


class Video(models.Model):
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name='videos'
    )
    playlist = models.ForeignKey(
        Playlist, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='videos'
    )
    title = models.CharField(max_length=512)          # без даты
    recorded_at = models.DateField(null=True, blank=True)   # дата из имени
    filename = models.CharField(max_length=512)       # оригинальное имя .mp4
    file_path = models.CharField(max_length=1024, unique=True)  # относительный
    thumbnail_path = models.CharField(max_length=1024, blank=True)  # .jpg
    duration = models.PositiveIntegerField(null=True, blank=True)   # секунды, позже
    size = models.BigIntegerField(default=0)          # байты
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-recorded_at', 'title']
        indexes = [
            models.Index(fields=['channel', 'playlist']),
            models.Index(fields=['recorded_at']),
            GinIndex(
                fields=['title'],
                name='video_title_trgm',
                opclasses=['gin_trgm_ops'],
            ),
        ]

    def __str__(self):
        return self.title


class Thumbnail(models.Model):
    video = models.OneToOneField(
        Video, on_delete=models.CASCADE, related_name='thumbnail'
    )
    file_path = models.CharField(max_length=1024)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f'Thumbnail for {self.video.title}'

class Audio(models.Model):
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name='audios'
    )
    playlist = models.ForeignKey(
        Playlist, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='audios'
    )

    title = models.CharField(max_length=512)
    recorded_at = models.DateField(null=True, blank=True)
    filename = models.CharField(max_length=512)
    file_path = models.CharField(max_length=1024, unique=True)
    cover_path = models.CharField(max_length=1024, blank=True)   # обложка
    duration = models.PositiveIntegerField(null=True, blank=True) # секунды
    size = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-recorded_at', 'title']
        indexes = [
            models.Index(fields=['channel', 'playlist']),
            models.Index(fields=['recorded_at']),
            GinIndex(
                fields=['title'],
                name='audio_title_trgm',
                opclasses=['gin_trgm_ops'],
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def cover_url(self):
        from django.conf import settings
        if not self.cover_path:
            return ''
        return f'{settings.MEDIA_URL}{self.cover_path}'

    @property
    def file_url(self):
        from django.conf import settings
        return f'{settings.MEDIA_URL}{self.file_path}'