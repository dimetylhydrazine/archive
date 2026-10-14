from django.contrib import admin
from .models import Channel, Playlist, Video, Thumbnail


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_visible')
    list_filter = ('is_visible',)
    list_editable = ('is_visible',)   # переключать прямо из списка
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel', 'parent')
    list_filter = ('channel',)
    search_fields = ('name',)
    autocomplete_fields = ('channel', 'parent')


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'channel', 'playlist', 'recorded_at', 'size')
    list_filter = ('channel', 'recorded_at')
    search_fields = ('title', 'filename')
    date_hierarchy = 'recorded_at'
    autocomplete_fields = ('channel', 'playlist')
    readonly_fields = ('file_path', 'thumbnail_path', 'size', 'created_at', 'updated_at')


@admin.register(Thumbnail)
class ThumbnailAdmin(admin.ModelAdmin):
    list_display = ('video', 'file_path', 'width', 'height')