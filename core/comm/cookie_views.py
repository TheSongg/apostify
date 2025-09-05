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
from .serializers import AccountSerializer
import asyncio
from playwright.async_api import async_playwright
from utils.comm import get_chrome_driver
from django.conf import settings
from asgiref.sync import sync_to_async
import json


logger = logging.getLogger(__name__)


class CookieViewSet(BaseViewSet):

    @action(detail=False, methods=['get'])
    def generate_xhs_cookie(self, request):
        # 在同步 view 中调用异步函数
        asyncio.run(self._async_generate_xiaohongshu_cookie())
        return Response("登录二维码保存成功！")

    async def _async_generate_xiaohongshu_cookie(self, nickname=None):
        try:
            async with async_playwright() as playwright:
                # 初始化浏览器
                browser, context, page = await self._init_browser(playwright)

                # 生成二维码
                qr_img_path = await self._generate_and_send_qr(page)

                # 使用 Telegram 机器人发送图片
                if os.getenv('USE_TELEGRAM_BOT') in ['True', True]:
                    await send_message.send_img_to_telegram(qr_img_path, '请扫描二维码登陆小红书！')

                # 等待扫码登录
                await self._wait_for_login(page)

                # 保存 cookie
                nickname = await self._save_cookie(context, nickname)

                await browser.close()
                logger.info("登录二维码保存成功！")
                await send_message.send_message_to_all_bot(f"{nickname}小红书Cookie更新成功~")
                await asyncio.to_thread(os.remove, qr_img_path)
        except Exception as e:
            logger.error(e)
            msg = f"{nickname or ''}小红书Cookie更新失败，错误：{e}"
            await send_message.send_message_to_all_bot(msg)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    async def _save_cookie(self, context, nickname=None):
        """异存 cookie 到数据库"""
        cookie = await context.storage_state()
        user_info = self.query_user_info(cookie)
        expiration_time = self.query_expiration_time(cookie)
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

        await self.update_account(data)
        return data['nickname']

    @sync_to_async
    def update_account(self, data, nickname):
        instance = Account.objects.filter(account_id=data.get('account_id', ''), nickname=nickname).first()
        if instance:
            self.db_save(AccountSerializer, data, instance)
        else:
            self.db_save(AccountSerializer, data)

    @staticmethod
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

    @staticmethod
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
