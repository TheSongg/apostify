import logging
from rest_framework.decorators import action
from rest_framework.response import Response
from core.comm.base_views import BaseViewSet
from core.comm.models import Videos, Account
from core.comm.serializers import VideosSerializer
import time
import os
from django.conf import settings
# from .task import upload_videos
import pytz


logger = logging.getLogger("xiaohongshu")


class VideoViewSet(BaseViewSet):
    serializer_class = VideosSerializer
    queryset = Videos.objects.all()
    platform_type = 1

    pass