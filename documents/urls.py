from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('documents/', views.document_list, name='document_list'),
    path('documents/channels/', views.channel_list, name='channel_list'),
    path('documents/channel/<slug:slug>/', views.channel_detail, name='channel_detail'),
    path('documents/playlist/<int:pk>/', views.playlist_detail, name='playlist_detail'),
]