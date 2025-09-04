from datetime import datetime
from core.comm import send_message
from pathlib import Path
import os
import logging
import base64
from utils.comm import set_init_script
from rest_framework.decorators import action
from rest_framework.response import Response
from core.comm.base_views import BaseViewSet
from .models import Account
import asyncio
from playwright.async_api import async_playwright
from utils.comm import get_chrome_driver


logger = logging.getLogger(__name__)


class CookieViewSet(BaseViewSet):

    @action(detail=False, methods=['get'])
    def generate_xhs_cookie(self, request):
        # 在同步 view 中调用异步函数
        asyncio.run(self._async_generate_xhs_cookie())
        return Response("登录二维码保存成功！")

    async def _async_generate_xhs_cookie(self):
        async with async_playwright() as playwright:
            # 异步初始化浏览器
            browser, context, page = await self._init_browser(playwright)

            # 异步生成二维码
            qr_img_path = await self._generate_and_send_qr(page)

            # 如果使用 Telegram 机器人发送图片（同步函数用 asyncio.to_thread）
            if os.getenv('USE_TG_BOT') in ['True', True]:
                await asyncio.to_thread(lambda: send_message.send_img_to_telegram(qr_img_path))

            # 异步等待扫码登录
            await self._wait_for_login(page)

            # 异步保存 cookie
            await self._save_cookie(context)

            await browser.close()
            logger.info("登录二维码保存成功！")

    @staticmethod
    async def _init_browser(playwright):
        """异步启动浏览器并初始化上下文"""
        # 异步获取浏览器实例
        browser = await get_chrome_driver(playwright)

        # 创建新上下文（异步）
        context = await browser.new_context()
        context = await set_init_script(context)

        # 创建新页面
        page = await context.new_page()

        # 打开主页
        await page.goto(os.getenv('XHS_HOME'))

        return browser, context, page

    @staticmethod
    async def _generate_and_send_qr(page):
        """异步点击登录并发送二维码到 Telegram"""
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

        # 保存二维码图片（文件写入可用 asyncio.to_thread 避免阻塞）
        _, b64data = src.split(",", 1)
        img_bytes = base64.b64decode(b64data)
        save_time = datetime.now().strftime("%Y%m%d%H%M%S")
        qr_img_path = Path(settings.BASE_DIR / "core/xiaohongshu/qr_img" / f"qr_img_{save_time}.png")

        await asyncio.to_thread(lambda: qr_img_path.parent.mkdir(parents=True, exist_ok=True))
        await asyncio.to_thread(lambda: qr_img_path.write_bytes(img_bytes))

        return qr_img_path

    @staticmethod
    async def _wait_for_login(page, max_wait=60, interval=3):
        """异步轮询等待用户扫码登录"""
        num = 0
        while num < max_wait:
            # 异步查询元素
            login_success = await page.query_selector("span:has-text('发布笔记')")
            if login_success:
                return

            # 异步等待
            await asyncio.sleep(interval)

            # 异步发送提示信息
            await asyncio.to_thread(lambda: send_message.send_message_to_telegram('请尽快扫码登录小红书！'))

            num += interval

        logger.error("登录超时，二维码未被扫描！")
        raise Exception("登录超时，二维码未被扫描！")

    @staticmethod
    async def _save_cookie(context):
        """异步保存 cookie 到数据库"""
        # 异步获取浏览器上下文的存储状态
        cookie = await context.storage_state()

        data = {
            "platform_type": 1,
            "account_id": cookie.get('account_id', ''),
            "nickname": cookie.get('nickname', ''),
            "password": cookie.get('password', ''),
            "phone": cookie.get('phone', ''),
            "email": cookie.get('email', ''),
            "cookie": cookie,
            "expiration_time": cookie.get('expiration_time', 0)
        }

        await asyncio.to_thread(lambda: Account.objects.create(**data))
