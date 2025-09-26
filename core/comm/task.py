from celery import shared_task
import time
import logging
from .models import Account
import importlib
from core.xiaohongshu.cookie import async_generate_xiaohongshu_cookie
from core.douyin.cookie import async_generate_douyin_cookie
from core.shipinhao.cookie import async_generate_shipinhao_cookie
from utils.static import PLATFORM_TYPE_CHOICES
from utils import config
import asyncio
from core.telegram.message import send_message


logger = logging.getLogger(__name__)


@shared_task
def refresh_cookies():
    """刷新cookie"""
    queryset = Account.objects.filter(is_available=True, expiration_time__gt=int(time.time())).all()
    error = []
    for account in queryset:
        platform = PLATFORM_TYPE_CHOICES[account.platform_type]
        module_path = f'core.{platform["en"]}.cookie'
        try:
            module = importlib.import_module(module_path)
            refresh_cookie_func = getattr(module, 'refresh_cookie')
            asyncio.run(refresh_cookie_func(account))
        except Exception as e:
            error.append(f"{platform['zh']}_{account.nickname}刷新cookie失败， 错误：{e}")

    error_msg = '\n'.join(error)
    asyncio.run(send_message(error_msg))


@shared_task
def generate_xiaohongshu_cookie(nickname=None):
    asyncio.run(async_generate_xiaohongshu_cookie(nickname))


@shared_task
def generate_douyin_cookie(nickname=None):
    asyncio.run(async_generate_douyin_cookie(nickname))


@shared_task
def generate_shipinhao_cookie(nickname=None):
    asyncio.run(async_generate_shipinhao_cookie(nickname))


@shared_task
def login_to_prevent_expiration():
    queryset = Account.objects.filter(is_available=True, expiration_time__gt=int(time.time())).all()
    for account in queryset:
        platform = PLATFORM_TYPE_CHOICES[account.platform_type]['en']
        url = getattr(config, f'{platform.upper()}_UPLOAD_PAGE')


