def index(request):
    from documents.models import Document
    from gallery.models import Image
    from videoplayer.models import Audio, Video

    return render(request, 'core/index.html', {
        'video_count': Video.objects.filter(channel__is_visible=True).count(),
        'audio_count': Audio.objects.filter(channel__is_visible=True).count(),
        'document_count': Document.objects.filter(enrich_failed=False).count(),
        'image_count': Image.objects.filter(enrich_failed=False).count(),
    })