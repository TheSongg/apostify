from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .video_views import VideoViewSet


router = DefaultRouter()
router.register(r'video', VideoViewSet, basename='video')


urlpatterns = [
    path('', include(router.urls)),
]