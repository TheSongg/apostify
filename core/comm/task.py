from celery import shared_task
import logging
from .models import Account
import importlib
from core.xiaohongshu.cookie import async_generate_xiaohongshu_cookie
from core.douyin.cookie import async_generate_douyin_cookie
from core.shipinhao.cookie import async_generate_shipinhao_cookie
from utils.static import PLATFORM_TYPE_CHOICES
import asyncio
from core.telegram.message import send_message
from asgiref.sync import sync_to_async
from django.db import connection


logger = logging.getLogger(__name__)


@sync_to_async
def get_active_accounts_sync():
    """安全地从数据库获取激活的账号列表。"""
    # 确保在新的线程中关闭旧的数据库连接，避免连接泄漏
    connection.close()
    return list(Account.objects.filter(is_available=True).all())


@sync_to_async
def get_platform_info_sync(account):
    """安全地获取平台信息，并关闭连接以防万一。"""
    connection.close()
    return PLATFORM_TYPE_CHOICES[account.platform_type]


@shared_task
def refresh_cookies():
    """Celery 定时任务：并发刷新所有活动的账号 Cookie"""

    async def async_main():
        queryset = await get_active_accounts_sync()
        check_tasks = []

        for account in queryset:
            platform = await get_platform_info_sync(account)
            module_path = f'core.{platform["en"]}.cookie'

            try:
                module = importlib.import_module(module_path)
                check_cookie_func = getattr(module, 'check_cookie')
                check_tasks.append(check_cookie_func(account))
            except Exception as e:
                # 处理导入模块失败的同步错误
                logger.error(f"导入 {platform['zh']} 模块失败: {e}")
        results = await asyncio.gather(*check_tasks, return_exceptions=True)

        error = []
        for i, result in enumerate(results):
            #  cookie的账号重新登录
            if isinstance(result, Exception):
                try:
                    account = queryset[i]
                    platform = await get_platform_info_sync(account)
                    module_path = f'core.{platform["en"]}.cookie'
                    module = importlib.import_module(module_path)
                    generate_cookie_func = getattr(module, 'generate_cookie')
                    await generate_cookie_func(account.phone)
                except Exception as e:
                    error.append(f"平台：[{platform['zh']}]，手机号：[{account.phone}]自动刷新cookie异常，错误：{e}")

        if error:
            await send_message('\n'.join(error))

    # 主异步函数，阻塞 Celery worker 直到所有并发操作完成
    asyncio.run(async_main())


@shared_task
def generate_xiaohongshu_cookie(login_phone):
    asyncio.run(async_generate_xiaohongshu_cookie(login_phone))


@shared_task
def generate_douyin_cookie(login_phone):
    asyncio.run(async_generate_douyin_cookie(login_phone))


@shared_task
def generate_shipinhao_cookie(login_phone):
    asyncio.run(async_generate_shipinhao_cookie(login_phone))
