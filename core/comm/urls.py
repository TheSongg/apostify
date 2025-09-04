from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .base_views import BaseViewSet
from .cookie_views import CookieViewSet
from .account_views import AccountViewSet


router = DefaultRouter()
router.register(r'', BaseViewSet, basename='')
router.register(r'cookie', CookieViewSet, basename='cookie')
router.register(r'account', AccountViewSet, basename='account')


urlpatterns = [
    path('', include(router.urls)),
]