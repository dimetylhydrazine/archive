from django.urls import path
from . import views

app_name = 'gallery'

urlpatterns = [
    path('gallery/', views.image_list, name='image_list'),
]