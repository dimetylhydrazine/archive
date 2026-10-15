# documents/admin.py
from django.contrib import admin
from .models import Channel, Playlist, Document, Category


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_visible')
    list_editable = ('is_visible',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel', 'parent')
    list_filter = ('channel',)

from django.contrib import admin
from .models import Channel, Playlist, Document, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'channel', 'recorded_at', 'enrich_failed')
    list_filter = ('channel', 'categories', 'recorded_at')
    search_fields = ('title', 'filename')
    filter_horizontal = ('categories',)   # ← удобный виджет M2M