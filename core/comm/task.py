from celery import shared_task
import datetime
import logging
from django.utils import timezone
from .models import Account
import sys
import asyncio
from core.xiaohongshu.cookie import async_generate_xiaohongshu_cookie
from core.douyin.cookie import async_generate_douyin_cookie


logger = logging.getLogger(__name__)


@shared_task
def check_and_refresh_cookies():
    """检测即将过期的 cookie 并刷新"""
    threshold = timezone.now() + datetime.timedelta(hours=1)
    timestamp = int(threshold.timestamp())
    expiring_accounts = Account.objects.filter(expiration_time__lte=timestamp, is_available=True)
    module = sys.modules[__name__]
    for account in expiring_accounts:
        try:
            platform_type = account.PLATFORM_TYPE_CHOICES[account.platform_type]['en']
            func = getattr(module, f"generate_{platform_type}_cookie")
            func.delay(account.nickname)

            logger.info(f"刷新成功: {account.nickname}")
        except Exception as e:
            logger.error(f"刷新失败: {account.nickname}, 错误: {e}")

@shared_task
def generate_xiaohongshu_cookie(nickname=None):
    asyncio.run(async_generate_xiaohongshu_cookie(nickname))


@shared_task
def generate_douyin_cookie(nickname=None):
    asyncio.run(async_generate_douyin_cookie(nickname))
