import random
from django.core.paginator import Paginator
from django.db.models import F, Func, Value, CharField, Count, Q
from django.shortcuts import render, get_object_or_404

from .models import Video, Channel, Playlist, Audio
from .search import search_model
from django.contrib.auth.decorators import login_required


PAGE_SIZE = 24


# ---------- Утилиты ----------

class MD5Random(Func):
    """md5(CONCAT(id, ':', seed)) — стабильный псевдослучайный ключ."""
    function = 'md5'
    template = "%(function)s(CONCAT(%(expressions)s))"
    arity = 2
    output_field = CharField()


def _shuffled_qs(request, model):
    """
    Возвращает queryset, отсортированный псевдослучайно,
    с seed в сессии (стабильно между страницами).
    """
    if 'shuffle_seed' not in request.session:
        request.session['shuffle_seed'] = random.randint(1, 2**31 - 1)
    seed = request.session['shuffle_seed']

    if request.GET.get('shuffle'):
        seed = random.randint(1, 2**31 - 1)
        request.session['shuffle_seed'] = seed

    qs = (
        model.objects
        .filter(channel__is_visible=True)
        .select_related('channel', 'playlist')
        .annotate(shuffle_key=MD5Random(F('id'), Value(f':{seed}')))
        .order_by('shuffle_key')
    )
    return qs, seed


def _paginate(request, qs, per_page=PAGE_SIZE):
    paginator = Paginator(qs, per_page)
    return paginator, paginator.get_page(request.GET.get('page'))


# ---------- Списки ----------

@login_required
def video_list(request):
    qs, seed = _shuffled_qs(request, Video)
    paginator, page_obj = _paginate(request, qs)
    return render(request, 'videoplayer/videos.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'shuffle_seed': seed,
    })

@login_required
def audio_list(request):
    qs, seed = _shuffled_qs(request, Audio)
    paginator, page_obj = _paginate(request, qs)
    return render(request, 'videoplayer/audio_list.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'shuffle_seed': seed,
    })

@login_required
def channel_list(request):
    channels = (
        Channel.objects
        .filter(is_visible=True)
        .annotate(
            videos_count=Count('videos', distinct=True),
            audios_count=Count('audios', distinct=True),
            playlists_count=Count('playlists', distinct=True),
        )
        .order_by('name')
    )
    return render(request, 'videoplayer/channel_list.html', {
        'channels': channels,
    })


# ---------- Детали ----------
@login_required
def channel_detail(request, slug):
    channel = get_object_or_404(Channel, slug=slug, is_visible=True)

    playlists = (
        channel.playlists
        .filter(parent__isnull=True)
        .annotate(
            videos_count=Count('videos', distinct=True),
            audios_count=Count('audios', distinct=True),
            children_count=Count('children', distinct=True),
        )
        .order_by('name')
    )

    # видео и аудио в корне канала — с пагинацией
    videos_qs = (
        channel.videos
        .filter(playlist__isnull=True)
        .select_related('playlist')
        .order_by('-recorded_at')
    )
    audios_qs = (
        channel.audios
        .filter(playlist__isnull=True)
        .select_related('playlist')
        .order_by('-recorded_at')
    )

    videos_paginator, videos_page = _paginate(request, videos_qs)
    audios_paginator, audios_page = _paginate(request, audios_qs)

    return render(request, 'videoplayer/channel_detail.html', {
        'channel': channel,
        'playlists': playlists,
        'videos_page': videos_page,
        'videos_paginator': videos_paginator,
        'audios_page': audios_page,
        'audios_paginator': audios_paginator,
        'total_videos': channel.videos.count(),
        'total_audios': channel.audios.count(),
    })

@login_required
def playlist_detail(request, pk):
    playlist = get_object_or_404(
        Playlist.objects.select_related('channel', 'parent'),
        pk=pk,
        channel__is_visible=True,
    )

    children = (
        playlist.children
        .annotate(
            videos_count=Count('videos', distinct=True),
            audios_count=Count('audios', distinct=True),
        )
        .order_by('name')
    )

    videos_qs = playlist.videos.select_related('channel').order_by('-recorded_at')
    audios_qs = playlist.audios.select_related('channel').order_by('-recorded_at')

    videos_paginator, videos_page = _paginate(request, videos_qs)
    audios_paginator, audios_page = _paginate(request, audios_qs)

    return render(request, 'videoplayer/playlist_detail.html', {
        'playlist': playlist,
        'children': children,
        'videos_page': videos_page,
        'videos_paginator': videos_paginator,
        'audios_page': audios_page,
        'audios_paginator': audios_paginator,
        'total_videos': playlist.videos.count(),
        'total_audios': playlist.audios.count(),
    })

@login_required
def video_detail(request, pk):
    video = get_object_or_404(
        Video.objects.select_related('channel', 'playlist'),
        pk=pk,
        channel__is_visible=True,
    )
    prev_video, next_video = _neighbors(video)
    return render(request, 'videoplayer/video_detail.html', {
        'video': video,
        'prev_video': prev_video,
        'next_video': next_video,
    })

@login_required
def audio_detail(request, pk):
    audio = get_object_or_404(
        Audio.objects.select_related('channel', 'playlist'),
        pk=pk,
        channel__is_visible=True,
    )
    prev_audio, next_audio = _neighbors(audio)
    return render(request, 'videoplayer/audio_detail.html', {
        'audio': audio,
        'prev_audio': prev_audio,
        'next_audio': next_audio,
    })


def _neighbors(item):
    """Соседние элементы по дате в том же канале."""
    if item.recorded_at is None:
        return None, None
    base = type(item).objects.filter(
        channel=item.channel,
        recorded_at__isnull=False,
    )
    prev_item = base.filter(recorded_at__gt=item.recorded_at).order_by('recorded_at').first()
    next_item = base.filter(recorded_at__lt=item.recorded_at).order_by('-recorded_at').first()
    return prev_item, next_item


from .search import search_model

@login_required
def search(request):
    q = request.GET.get('q', '').strip()
    videos = Video.objects.none()
    audios = Audio.objects.none()

    if q:
        videos = search_model(Video, q)
        audios = search_model(Audio, q)

    total = len(videos) + len(audios)

    return render(request, 'videoplayer/search.html', {
        'q': q,
        'videos': videos,
        'audios': audios,
        'total': total,
    })