from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Channel(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    path = models.CharField(max_length=1024)
    is_visible = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'канал'
        verbose_name_plural = 'каналы'

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
    path = models.CharField(max_length=1024)

    class Meta:
        ordering = ['name']
        unique_together = [('channel', 'parent', 'name')]
        verbose_name = 'плейлист'
        verbose_name_plural = 'плейлисты'

    def __str__(self):
        return self.name


class Document(models.Model):
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name='documents'
    )
    playlist = models.ForeignKey(
        Playlist, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='documents'
    )

    categories = models.ManyToManyField(   # ← ДОБАВИТЬ СЮДА
        Category, blank=True, related_name='documents'
    )

    title = models.CharField(max_length=512)
    author = models.CharField(max_length=255, blank=True)
    recorded_at = models.DateField(null=True, blank=True)
    filename = models.CharField(max_length=512)
    file_path = models.CharField(max_length=1024, unique=True)
    cover_path = models.CharField(max_length=1024, blank=True)
    pages = models.PositiveIntegerField(null=True, blank=True)
    size = models.BigIntegerField(default=0)
    is_broken = models.BooleanField(default=False, db_index=True)
    enrich_failed = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-recorded_at', 'title']
        indexes = [
            models.Index(fields=['channel', 'playlist']),
            models.Index(fields=['recorded_at']),
        ]
        verbose_name = 'документ'
        verbose_name_plural = 'документы'

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

