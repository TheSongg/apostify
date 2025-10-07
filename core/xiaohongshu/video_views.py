import logging
from rest_framework.decorators import action
from rest_framework.response import Response
from core.comm.base_views import BaseViewSet
from core.comm.models import Videos, Account
from core.comm.serializers import VideosSerializer
import time
import os
from django.conf import settings
from .task import upload_videos
import pytz
from utils.static import PlatFormType
from core.users.exception import APException


logger = logging.getLogger("xiaohongshu")


class VideoViewSet(BaseViewSet):
    serializer_class = VideosSerializer
    queryset = Videos.objects.all()
    platform_type = PlatFormType.xiaohongshu.value

    @staticmethod
    def set_schedule_time(page, publish_date):
        # 点击 "定时发布" 复选框
        label_element = page.locator("label:has-text('定时发布')")
        label_element.click()
        time.sleep(1)
        publish_date_hour = publish_date.strftime("%Y-%m-%d %H:%M")
        time.sleep(1)
        page.locator('.el-input__inner[placeholder="选择日期和时间"]').click()
        page.keyboard.press("Control+A")
        page.keyboard.type(str(publish_date_hour))
        page.keyboard.press("Enter")
        time.sleep(1)

    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request, *args, **kwargs):
        logger.info(f'func:upload, param: {request.data}')
        title = request.data.get("title", "")
        tags = request.data.get("tags", [])
        video_name = request.data.get("video_name")
        nickname = request.data.get("nickname")

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
            raise APException('该小红书账号不可用，请先添加账号并生成Cookie！')

        month_dir_str = instance.upload_time.astimezone(
            pytz.timezone(settings.TIME_ZONE)
        ).strftime("%Y-%m")
        file_path = os.path.join(settings.BASE_DIR, "videos", month_dir_str, video_name)

        upload_videos.delay(nickname, self.platform_type, file_path, title, tags, video_name)
        return Response('后台上传中，稍后请注意查看上传结果！')
