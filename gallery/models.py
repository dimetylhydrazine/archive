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


class Image(models.Model):
    categories = models.ManyToManyField(
        Category, blank=True, related_name='images'
    )

    title = models.CharField(max_length=512)
    recorded_at = models.DateField(null=True, blank=True)
    filename = models.CharField(max_length=512)
    file_path = models.CharField(max_length=1024, unique=True)
    thumb_path = models.CharField(max_length=1024, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    size = models.BigIntegerField(default=0)
    is_broken = models.BooleanField(default=False, db_index=True)
    enrich_failed = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-recorded_at', 'title']
        indexes = [
            models.Index(fields=['recorded_at']),
        ]
        verbose_name = 'изображение'
        verbose_name_plural = 'изображения'

    def __str__(self):
        return self.title

    @property
    def thumb_url(self):
        from django.conf import settings
        if not self.thumb_path:
            return ''
        return f'{settings.MEDIA_URL}{self.thumb_path}'

    @property
    def file_url(self):
        from django.conf import settings
        return f'{settings.MEDIA_URL}{self.file_path}'