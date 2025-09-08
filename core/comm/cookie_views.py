import logging
from rest_framework.decorators import action
from rest_framework.response import Response
from core.comm.base_views import BaseViewSet
from .task import generate_xiaohongshu_cookie, generate_douyin_cookie, generate_shipinhao_cookie


logger = logging.getLogger(__name__)


class CookieViewSet(BaseViewSet):

    @action(detail=False, methods=['post'])
    def generate_xhs_cookie(self, request):
        nickname = request.data.get('nickname', None)
        generate_xiaohongshu_cookie.delay(nickname)
        return Response("后台执行中~")

    @action(detail=False, methods=['post'])
    def generate_douyin_cookie(self, request):
        nickname = request.data.get('nickname', None)
        generate_douyin_cookie.delay(nickname)
        return Response("后台执行中~")

    @action(detail=False, methods=['post'])
    def generate_shipinhao_cookie(self, request):
        nickname = request.data.get('nickname', None)
        generate_shipinhao_cookie.delay(nickname)
        return Response("后台执行中~")
