import logging
from rest_framework.decorators import action
from rest_framework.response import Response
from core.comm.base_views import BaseViewSet
from .task import generate_cookie
from utils.static import PlatFormType


logger = logging.getLogger(__name__)


class CookieViewSet(BaseViewSet):

    @action(detail=False, methods=['post'])
    def generate_xiaohongshu_cookie(self, request):
        login_phone = request.data.get('phone', None)
        if not login_phone:
            raise Exception('手机号输入错误！')
        generate_cookie.delay(login_phone, PlatFormType.xiaohongshu.value)
        return Response("后台执行中~")

    @action(detail=False, methods=['post'])
    def generate_douyin_cookie(self, request):
        login_phone = request.data.get('phone', None)
        if not login_phone:
            raise Exception('手机号输入错误！')
        generate_cookie.delay(login_phone, PlatFormType.douyin.value)
        return Response("后台执行中~")

    @action(detail=False, methods=['post'])
    def generate_shipinhao_cookie(self, request):
        login_phone = request.data.get('phone', None)
        if not login_phone:
            raise Exception('手机号输入错误！')
        generate_cookie.delay(login_phone, PlatFormType.shipinhao.value)
        return Response("后台执行中~")
