# gallery/admin.py
from django.contrib import admin

from .models import Category, Image


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'recorded_at', 'width', 'height', 'enrich_failed')
    list_filter = ('categories', 'recorded_at')
    search_fields = ('title', 'filename')
    filter_horizontal = ('categories',)