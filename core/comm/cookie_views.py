import logging
from rest_framework.decorators import action
from rest_framework.response import Response
from core.comm.base_views import BaseViewSet
from .task import generate_xiaohongshu_cookie, generate_douyin_cookie, generate_shipinhao_cookie


logger = logging.getLogger(__name__)


class CookieViewSet(BaseViewSet):

    @action(detail=False, methods=['post'])
    def generate_xiaohongshu_cookie(self, request):
        login_phone = request.data.get('phone', None)
        if not login_phone:
            raise Exception('手机号输入错误！')
        generate_xiaohongshu_cookie.delay(login_phone)
        return Response("后台执行中~")

    @action(detail=False, methods=['post'])
    def generate_douyin_cookie(self, request):
        login_phone = request.data.get('phone', None)
        if not login_phone:
            raise Exception('手机号输入错误！')
        generate_douyin_cookie.delay(login_phone)
        return Response("后台执行中~")

    @action(detail=False, methods=['post'])
    def generate_shipinhao_cookie(self, request):
        login_phone = request.data.get('phone', None)
        if not login_phone:
            raise Exception('手机号输入错误！')
        generate_shipinhao_cookie.delay(login_phone)
        return Response("后台执行中~")
