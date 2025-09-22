from django.http import JsonResponse
from rest_framework import status
from django.conf import settings
from asgiref.sync import sync_to_async
from pathlib import Path
import os
import base64
import logging
import datetime
from core.comm.serializers import AccountSerializer
import asyncio
from django.db import transaction
import time
from core.comm.models import Videos, Account, VerificationCode


logger = logging.getLogger(__name__)


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
    stealth_js_path = Path(settings.BASE_DIR) / "utils" / "stealth.min.js"
    await context.add_init_script(path=str(stealth_js_path))
    return context

async def get_chrome_driver(playwright):
    chrome_driver = os.getenv('CHROME_DRIVER')

    if chrome_driver.startswith('ws://') or \
        chrome_driver.startswith('http://'):
        # 连接已经运行的 Playwright Server
        return await playwright.chromium.connect(chrome_driver)
        # 本地启动浏览器
    return await playwright.chromium.launch(
        headless=True if os.getenv('HEADLESS') in ['True', True] else False,
        executable_path=chrome_driver
    )

async def init_browser(playwright, cookie=None):
    """异步启动浏览器并初始化上下文"""
    # 获取浏览器实例
    browser = await get_chrome_driver(playwright)

    # 创建新上下文
    args = generate_new_context_args(cookie=cookie)

    context = await browser.new_context(**args)
    context = await set_init_script(context)

    # 创建新页面
    page = await context.new_page()
    page.set_default_timeout(int(os.getenv('DEFAULT_TIMEOUT')))
    page.set_default_navigation_timeout(int(os.getenv('DEFAULT_TIMEOUT')))

    return browser, context, page

def generate_new_context_args(cookie):
    args = {}
    if os.getenv('HEADLESS') in ['True', True]:
        args['viewport'] = {"width": int(os.getenv('WIDTH')), "height": int(os.getenv('HEIGHT'))}

    if cookie is not None:
        args["storage_state"] = cookie

    return args


async def save_qr(src, path_name):
    # 保存二维码图片
    _, b64data = src.split(",", 1)
    img_bytes = base64.b64decode(b64data)
    save_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    qr_img_path = Path(settings.BASE_DIR / "qr_img" / f"{path_name}_{save_time}.png")

    await asyncio.to_thread(lambda: qr_img_path.parent.mkdir(parents=True, exist_ok=True))
    await asyncio.to_thread(lambda: qr_img_path.write_bytes(img_bytes))
    return qr_img_path


@sync_to_async
def update_account(data):
    instance = Account.objects.filter(account_id=data.get('account_id', ''), nickname=data.get('nickname')).first()
    if not instance:
        serializer = AccountSerializer(data=data)
    else:
        serializer = AccountSerializer(instance, data=data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()


def query_expiration_time(cookie):
    expiration_time_list = []
    try:
        cookies = cookie['cookies']
        for item in cookies:
            if item.get('expires', 0) > 1:
                expiration_time_list.append(item.get('expires'))
        return int(min(expiration_time_list))
    except Exception as e:
        raise Exception(f'查询expiration_time异常，错误：{str(e)}')


def associated_account_and_video(account, video_name):
    with transaction.atomic():
        video_instance = Videos.objects.select_for_update().get(name=video_name)
        video_instance.account.add(account)


async def close_browser_context(browser, context):
    try:
        if context:
            await context.close()
        if browser:
            await browser.close()
    except Exception as e:
        logger.debug(f"关闭 browser、context 出错: {e}")

@sync_to_async
def get_code_instance():
    for i in range(60):
        time.sleep(1)
        code_instance = VerificationCode.objects.first()
        if code_instance:
            return code_instance

    raise Exception("验证码异常或未收到验证码！")

@sync_to_async
def delete_code_instance():
    old_instances = VerificationCode.objects.all()
    if old_instances:
        for instance in old_instances:
            instance.delete()
