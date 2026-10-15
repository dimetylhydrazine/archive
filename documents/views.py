from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.db.models import Count

from .models import Document, Channel, Playlist, Category


from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404


def document_list(request):
    category_slug = request.GET.get('category', '').strip()

    qs = (
        Document.objects
        .filter(channel__is_visible=True, enrich_failed=False)
        .select_related('channel', 'playlist')
        .prefetch_related('categories')
        .order_by('-recorded_at')
    )

    current_category = None
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        qs = qs.filter(categories=current_category)

    paginator = Paginator(qs, 24)
    page_obj = paginator.get_page(request.GET.get('page'))

    categories = Category.objects.annotate(
        documents_count=Count('documents', distinct=True)
    ).order_by('name')

    return render(request, 'documents/document_list.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'categories': categories,
        'current_category': current_category,
    })

def channel_list(request):
    channels = (
        Channel.objects
        .filter(is_visible=True)
        .annotate(
            documents_count=Count('documents', distinct=True),
            playlists_count=Count('playlists', distinct=True),
        )
        .order_by('name')
    )
    return render(request, 'documents/channel_list.html', {'channels': channels})


def channel_detail(request, slug):
    channel = get_object_or_404(Channel, slug=slug, is_visible=True)

    playlists = (
        channel.playlists
        .filter(parent__isnull=True)
        .annotate(
            documents_count=Count('documents', distinct=True),
            children_count=Count('children', distinct=True),
        )
        .order_by('name')
    )
    documents = (
        channel.documents
        .filter(playlist__isnull=True, enrich_failed=False)
        .order_by('-recorded_at')
    )

    return render(request, 'documents/channel_detail.html', {
        'channel': channel,
        'playlists': playlists,
        'documents': documents,
        'total_documents': channel.documents.count(),
    })


def playlist_detail(request, pk):
    playlist = get_object_or_404(
        Playlist.objects.select_related('channel', 'parent'),
        pk=pk, channel__is_visible=True,
    )
    children = (
        playlist.children
        .annotate(documents_count=Count('documents', distinct=True))
        .order_by('name')
    )
    documents = (
        playlist.documents
        .filter(enrich_failed=False)
        .order_by('-recorded_at')
    )
    return render(request, 'documents/playlist_detail.html', {
        'playlist': playlist,
        'children': children,
        'documents': documents,
        'total_documents': playlist.documents.count(),
    })

from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render, get_object_or_404

from .models import Document, Category
from .search import search_documents


def document_search(request):
    q = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()

    qs = Document.objects.none()
    if q:
        qs = search_documents(q, limit=200)
        if category_slug:
            current_cat = get_object_or_404(Category, slug=category_slug)
            qs = qs.filter(categories=current_cat)

    paginator = Paginator(qs, 24)
    page_obj = paginator.get_page(request.GET.get('page'))

    categories = Category.objects.annotate(
        documents_count=Count('documents', distinct=True)
    ).order_by('name')

    return render(request, 'documents/document_search.html', {
        'q': q,
        'page_obj': page_obj,
        'paginator': paginator,
        'categories': categories,
        'current_category': get_object_or_404(Category, slug=category_slug) if category_slug else None,
    })