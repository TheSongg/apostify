from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .base_views import BaseViewSet


router = DefaultRouter()
router.register(r'', BaseViewSet, basename='')


urlpatterns = [
    path('', include(router.urls)),
]