import logging
from rest_framework.decorators import action
from rest_framework.response import Response
from core.comm.base_views import BaseViewSet
from core.comm.models import Videos, Account
from core.comm.serializers import VideosSerializer
from core.users.exception import APException
import os
from django.conf import settings
from .task import upload_videos
import pytz
from utils.static import PlatFormType


logger = logging.getLogger("shipinhao")


class VideoViewSet(BaseViewSet):
    serializer_class = VideosSerializer
    queryset = Videos.objects.all()
    platform_type = PlatFormType.shipinhao.value

    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request, *args, **kwargs):
        logger.info(f'func:upload, param: {request.data}')
        title = request.data.get("title", "")
        tags = request.data.get("tags", [])
        video_name = request.data.get("video_name")
        nickname = request.data.get("nickname")
        category = request.data.get("category", None)

        if not video_name:
            raise APException('视频名称不能为空！')

        instance = self.queryset.filter(name=video_name).first()
        if not instance:
            raise APException(f'视频{video_name}不存在！')

        account = Account.objects.filter(
            platform_type=self.platform_type,
            is_available=True,
            nickname=nickname
        )
        if not account.exists():
            raise APException('该视频号账号不可用，请先添加账号并生成Cookie！')

        month_dir_str = instance.upload_time.astimezone(
            pytz.timezone(settings.TIME_ZONE)
        ).strftime("%Y-%m")
        file_path = os.path.join(settings.BASE_DIR, "videos", month_dir_str, video_name)

        upload_videos.delay(nickname, self.platform_type, file_path, title, tags, video_name, category)
        return Response('后台上传中，稍后请注意查看上传结果！')
