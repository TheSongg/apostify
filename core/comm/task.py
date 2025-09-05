from celery import shared_task
import datetime
import logging
from django.utils import timezone
from playwright.async_api import async_playwright
from utils.comm import get_chrome_driver
from django.conf import settings
from asgiref.sync import sync_to_async
from datetime import datetime
from core.comm import send_message
from pathlib import Path
import os
import base64
from utils.comm import set_init_script
from .models import Account
from .serializers import AccountSerializer
import json
import sys
import asyncio


logger = logging.getLogger(__name__)


@shared_task
def check_and_refresh_cookies():
    """检测即将过期的 cookie 并刷新"""
    threshold = timezone.now() + datetime.timedelta(hours=1)
    expiring_accounts = Account.objects.filter(expiration_time__lte=threshold, is_available=True)
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

async def async_generate_xiaohongshu_cookie(nickname):
    try:
        async with async_playwright() as playwright:
            # 初始化浏览器
            browser, context, page = await _init_browser(playwright)

            # 生成二维码
            qr_img_path = await _generate_and_send_qr(page)

            # 使用 Telegram 机器人发送图片
            if os.getenv('USE_TELEGRAM_BOT') in ['True', True]:
                await send_message.send_img_to_telegram(qr_img_path, '请扫描二维码登陆小红书！')

            # 等待扫码登录
            await _wait_for_login(page)

            # 保存 cookie
            nickname = await _save_cookie(context, nickname)

            await browser.close()
            logger.info("登录二维码保存成功！")
            await send_message.send_message_to_all_bot(f"{nickname}小红书Cookie更新成功~")
            await asyncio.to_thread(os.remove, qr_img_path)
    except Exception as e:
        logger.error(e)
        msg = f"{nickname or ''}小红书Cookie更新失败，错误：{e}"
        await send_message.send_message_to_all_bot(msg)


async def _init_browser(playwright):
    """异步启动浏览器并初始化上下文"""
    # 获取浏览器实例
    browser = await get_chrome_driver(playwright)

    # 创建新上下文
    context = await browser.new_context()
    context = await set_init_script(context)

    # 创建新页面
    page = await context.new_page()
    page.set_default_timeout(int(os.getenv('DEFAULT_TIMEOUT')))
    page.set_default_navigation_timeout(int(os.getenv('DEFAULT_TIMEOUT')))

    # 打开主页
    await page.goto(os.getenv('XHS_HOME'))

    return browser, context, page


async def _generate_and_send_qr(page):
    """点击登录并发送二维码到 Telegram"""
    # 点击登录按钮
    await page.locator("img.css-wemwzq").click()

    # 等待二维码加载
    img = page.locator("img.css-1lhmg90")
    await page.wait_for_selector("img.css-1lhmg90")

    # 获取二维码 src
    src = await img.get_attribute("src")
    if not (src and src.startswith("data:image")):
        logger.error("未找到登录二维码！")
        raise Exception("未找到登录二维码！")

    # 保存二维码图片
    _, b64data = src.split(",", 1)
    img_bytes = base64.b64decode(b64data)
    save_time = datetime.now().strftime("%Y%m%d%H%M%S")
    qr_img_path = Path(settings.BASE_DIR / "core/xiaohongshu/qr_img" / f"qr_img_{save_time}.png")

    await asyncio.to_thread(lambda: qr_img_path.parent.mkdir(parents=True, exist_ok=True))
    await asyncio.to_thread(lambda: qr_img_path.write_bytes(img_bytes))

    return qr_img_path


async def _wait_for_login(page, max_wait=60, interval=3):
    """轮询等待用户扫码登录"""
    num = 0
    while num < max_wait:
        # 查询元素
        login_success = await page.query_selector("span:has-text('发布笔记')")
        if login_success:
            return

        await asyncio.sleep(interval)
        num += interval

    logger.error("登录超时，二维码未被扫描！")
    raise Exception("登录超时，二维码未被扫描！")

async def _save_cookie(context, nickname=None):
    """异存 cookie 到数据库"""
    cookie = await context.storage_state()
    user_info = query_user_info(cookie)
    expiration_time = query_expiration_time(cookie)
    data = {
        "platform_type": 1,
        "account_id": user_info.get('redId', ''),
        "nickname": user_info.get('userName', ''),
        "password": user_info.get('password', ''),
        "phone": user_info.get('phone', ''),
        "email": user_info.get('email', ''),
        "cookie": cookie,
        "expiration_time": expiration_time
    }
    if nickname is not None:
        if nickname != data['nickname']:
            raise Exception(f'请使用{nickname}账号扫码登录！')

    await update_account(data, nickname)
    return data['nickname']

@sync_to_async
def update_account(data, nickname):
    instance = Account.objects.filter(account_id=data.get('account_id', ''), nickname=nickname).first()
    if not instance:
        serializer = AccountSerializer(data=data)
    else:
        serializer = AccountSerializer(instance, data=data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

def query_user_info(cookie):
    try:
        local_storage = cookie['origins'][0].get('localStorage', [])
        user_info = None
        for item in local_storage:
            if item.get('name') == 'USER_INFO_FOR_BIZ':
                user_info = item.get('value')
                break
        if user_info is None:
            raise Exception('不存在USER_INFO_FOR_BIZ字段！')

        if isinstance(user_info, str):
            user_info = json.loads(user_info)
        return user_info
    except Exception as e:
        raise Exception(f'查询user_info异常，错误：{str(e)}')

def query_expiration_time(cookie):
    expiration_time_list = []
    try:
        cookies = cookie['cookies']
        for item in cookies:
            if item.get('expires'):
                expiration_time_list.append(item.get('expires'))
        return int(min(expiration_time_list))
    except Exception as e:
        raise Exception(f'查询expiration_time异常，错误：{str(e)}')
