
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, render

from .models import Category, Image


def image_list(request):
    category_slug = request.GET.get('category', '').strip()

    qs = (
        Image.objects
        .filter(enrich_failed=False)
        .prefetch_related('categories')
        .order_by('-recorded_at')
    )

    current_category = None
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        qs = qs.filter(categories=current_category)

    paginator = Paginator(qs, 60)   # 60 картинок на страницу
    page_obj = paginator.get_page(request.GET.get('page'))

    categories = Category.objects.annotate(
        images_count=Count('images', distinct=True)
    ).order_by('name')

    return render(request, 'gallery/image_list.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'categories': categories,
        'current_category': current_category,
        'MEDIA_URL': settings.MEDIA_URL,
    })