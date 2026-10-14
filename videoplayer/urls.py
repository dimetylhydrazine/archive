from django.urls import path
from . import views

app_name = 'videoplayer'

urlpatterns = [
    path('', views.video_list, name='video_list'),
    path('video/<int:pk>/', views.video_detail, name='video_detail'),
    path('channels/', views.channel_list, name='channel_list'),
    path('playlist/<int:pk>/', views.playlist_detail, name='playlist_detail'),
    path('channel/<slug:slug>/', views.channel_detail, name='channel_detail'),
    path('audio/', views.audio_list, name='audio_list'),
    path('audio/<int:pk>/', views.audio_detail, name='audio_detail'),
    path('search/', views.search, name='search'),
]