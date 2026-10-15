def index(request):
    from videoplayer.models import Video, Audio
    from documents.models import Document
    from gallery.models import Image

    return render(request, 'core/index.html', {
        'video_count': Video.objects.filter(channel__is_visible=True).count(),
        'audio_count': Audio.objects.filter(channel__is_visible=True).count(),
        'document_count': Document.objects.filter(enrich_failed=False).count(),
        'image_count': Image.objects.filter(enrich_failed=False).count(),
    })