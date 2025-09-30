import threading
from logging.config import dictConfig
from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
from urllib.parse import unquote


thread_user_data = {}

dictConfig(settings.LOGGING)
ls = threading.local()


def set_thread_user_data(username, ip, language, cn="", user_obj=None, permissions=None):
    ls.key = username + ip
    ls.name = username
    ls.ip = ip
    ls.language = language
    ls.cn = cn
    ls.user_obj = user_obj
    ls.permissions = permissions


def get_thread_language():
    if hasattr(ls, "language"):
        return ls.language
    else:
        return settings.LANGUAGE_CODE


def get_http_head_parm(request, param):
    try:
        param = 'HTTP_' + param.upper()
        return unquote(request.META.get(param))
    except:
        return 'zh'


def get_http_ip(request):
    try:
        # 判断是否有代理，以便于获取真实ip，而不是nginx所代理的本地ip
        if request.META.get('HTTP_X_FORWARDED_FOR'):
            ip = request.META.get("HTTP_X_FORWARDED_FOR")
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
    except:
        raise Exception("未检测请求源IP！")


def http_response_data(data, code="", message="", advice=""):
    return {
        "code": code,
        "message": message,
        "data": data
    }


def json_rsp(data=None, http_status=status.HTTP_200_OK):
    """
    正常响应：将参数组装成固定的JSON格式并发送。
    """
    response_data = http_response_data(data)
    response = JsonResponse(response_data, safe=False, status=http_status, json_dumps_params={'ensure_ascii': False})
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response["Access-Control-Max-Age"] = "1000"
    response["Access-Control-Allow-Headers"] = "*"
    return response


def json_err_rsp(exception, http_status=status.HTTP_200_OK):
    error_code = "0001"
    error_msg = str(exception)
    rsp_status = http_status
    response_data = http_response_data(None, error_code, error_msg)
    response = JsonResponse(response_data, safe=False, status=rsp_status, json_dumps_params={'ensure_ascii': False})
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response["Access-Control-Max-Age"] = "1000"
    response["Access-Control-Allow-Headers"] = "*"
    return response