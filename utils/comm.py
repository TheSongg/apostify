from django.http import JsonResponse
from rest_framework import status
from django.conf import settings
from pathlib import Path
import os


def field_en_to_zh(instance, data):
    res = {}
    for key, value in data.items():
        new_key = instance._meta.get_field(key).verbose_name
        res[new_key] = value

    return res

def dict_to_str(data):
    res = []
    for key, value in data.items():
        if '/' in key:
            key = key.split('/')[1]
        res.append(f"{key}:{value}")
    return ";".join(res)


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

async def set_init_script(context):
    stealth_js_path = Path(settings.BASE_DIR) / "core" / "utils" / "stealth.min.js"
    await context.add_init_script(path=str(stealth_js_path))
    return context

async def get_chrome_driver(playwright):
    chrome_driver = os.getenv('CHROME_DRIVER')

    if chrome_driver.startswith('ws://') or \
        chrome_driver.startswith('http://'):
        # 连接已经运行的 Playwright Server
        return await playwright.chromium.connect_over_cdp(chrome_driver)
        # 本地启动浏览器
    return await playwright.chromium.launch(
        headless=True if os.getenv('HEADLESS') in ['True', True] else False,
        executable_path=chrome_driver
    )
