from rest_framework.decorators import action
from rest_framework.response import Response
from core.comm.base_views import BaseViewSet
from .task import generate_cookie
from utils.static import PLATFORM_TYPE_CHOICES
from core.comm.models import VerificationCode, Account
import re
from core.users.exception import APException
import logging


logger = logging.getLogger("app")


class CookieViewSet(BaseViewSet):

    @action(detail=False, methods=['post'])
    def generate_cookie(self, request):
        logger.info(f'func:generate_cookie, param: {request.data}')
        login_phone = request.data.get('phone', None)
        platform_type = int(request.data.get('platform_type', 0))
        if not login_phone:
            raise APException('手机号或邮箱输入错误！')

        if platform_type not in PLATFORM_TYPE_CHOICES:
            raise APException('平台类型错误！')

        if Account.objects.filter(
            platform_type=platform_type,
            is_available=True,
        ).exists():
            raise APException('已存在同平台账号，当前版本一个平台只支持维护一个账号信息！')

        generate_cookie.delay(login_phone, platform_type)
        return Response("后台执行中~")


    @action(detail=False, methods=['get'])
    def fill_in_code(self, request, *args, **kwargs):
        logger.info(f'func:fill_in_code, param: {self.request.GET}')
        text = self.request.GET.get('text')
        if not text:
            raise APException("文本不能为空！")

        pattern = r"\b(\d{6}|\d{4})\b"
        matches = re.findall(pattern, text)
        if not matches:
            raise APException("文本内容异常，未检测到验证码！")

        old_instances = VerificationCode.objects.all()
        if old_instances:
            for instance in old_instances:
                instance.delete()
        VerificationCode.objects.create(code=str(matches[0]).strip())
        return Response({"status": "success"})
