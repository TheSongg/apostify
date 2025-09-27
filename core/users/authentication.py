from rest_framework.authentication import BaseAuthentication
import logging
from django.conf import settings
import os
from utils.comm import get_http_head_parm


logger = logging.getLogger(__name__)


class UserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if self.check_request_is_whitelist(request._request, settings.WHITELIST_URL):
            return
        elif self.check_request_is_whitelist(request._request, settings.CUSTOM_URL):
            auth = request._request.GET.get('auth')
            if auth != os.getenv('X_API_KEY'):
                raise Exception("鉴权失败！")
        else:
            api_key = get_http_head_parm(request._request, 'X_API_KEY')
            if api_key != os.getenv('X_API_KEY'):
                raise Exception('鉴权失败！')
            return

    def check_request_is_whitelist(self, request, param) -> bool:
        """
        判断请求的url是否为白名单权限路由
        :param request: 请求的url
        :param param: 白名单url
        :return: bool，请求url为白名单时，返回True，否则返回False
        """
        for url in param:
            if self.check_url_and_request(url, request):
                return True
        return False

    @staticmethod
    def check_url_and_request(permit_url, request):
        if request.method != permit_url["method"]:
            return False
        permit_url, request_url = permit_url["url"].split("/")[1:], request.path.split("/")[1:]
        if len(permit_url) != len(request_url):
            return False
        for index, value in enumerate(permit_url):
            if (not (value.startswith("<") and value.endswith(">"))) and value != request_url[index]:
                return False
        return True
