import logging
from rest_framework.decorators import action
from rest_framework.response import Response
from utils.base_views import BaseViewSet
from utils.comm import set_init_script
from core.comm.models import Videos, Account
from core.comm.serializers import VideosSerializer
from playwright.sync_api import sync_playwright
import time
from pathlib import Path
import os
import base64
from django.conf import settings
from datetime import datetime
from core.comm import send_message
from .task import upload_videos


logger = logging.getLogger("xiaohongshu")


class VideoViewSet(BaseViewSet):
    serializer_class = VideosSerializer
    queryset = Videos.objects.all()
    platform_type = 1

    @staticmethod
    def set_schedule_time(page, publish_date):
        # 点击 "定时发布" 复选框
        label_element = page.locator("label:has-text('定时发布')")
        label_element.click()
        time.sleep(1)
        publish_date_hour = publish_date.strftime("%Y-%m-%d %H:%M")
        time.sleep(1)
        page.locator('.el-input__inner[placeholder="选择日期和时间"]').click()
        page.keyboard.press("Control+A")
        page.keyboard.type(str(publish_date_hour))
        page.keyboard.press("Enter")
        time.sleep(1)

    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request, *args, **kwargs):
        title = request.data.get("title", "")
        tags = request.data.get("tags", [])
        file_path = request.data.get("file_path")

        if not file_path:
            raise Exception('视频路径不能为空！')

        accounts = Account.objects.filter(platform_type=self.platform_type, is_available=True)
        upload_videos.delay(accounts, file_path, title, tags)
        return Response('后台上传中，稍后请注意查看上传结果！')


    @action(detail=False, methods=['get'])
    def generate_cookie(self, request):
        with sync_playwright() as playwright:
            browser, context, page = self._init_browser(playwright)

            # 生成并发送二维码
            qr_img_path = self._generate_and_send_qr(page)
            # 发送到 Telegram
            if os.getenv('USE_TG_BOT') in ['True', True]:
                send_message.send_img_to_telegram(qr_img_path)
            # 等待扫码登录
            self._wait_for_login(page)
            # 保存 cookie
            self._save_cookie(context)

            browser.close()
            logger.info("登录二维码保存成功！")
            return Response("登录二维码保存成功！")

    @staticmethod
    def _init_browser(playwright):
        """启动浏览器并初始化上下文"""
        browser = playwright.chromium.launch(
            executable_path=os.getenv('CHROME_DRIVER'),
            headless=os.getenv('HEADLESS')
        )
        context = browser.new_context()
        context = set_init_script(context)
        page = context.new_page()
        page.goto(os.getenv('XHS_HOME'))
        return browser, context, page

    @staticmethod
    def _generate_and_send_qr(page):
        """点击登录并发送二维码到 Telegram"""
        page.locator("img.css-wemwzq").click()
        img = page.locator("img.css-1lhmg90")
        page.wait_for_selector("img.css-1lhmg90")

        src = img.get_attribute("src")
        if not (src and src.startswith("data:image")):
            logger.error("未找到登录二维码！")
            raise Exception("未找到登录二维码！")

        # 保存二维码图片
        _, b64data = src.split(",", 1)
        img_bytes = base64.b64decode(b64data)
        save_time = datetime.now().strftime("%Y%m%d%H%M%S")
        qr_img_path = Path(settings.BASE_DIR / "core/xiaohongshu/qr_img" / f"qr_img_{save_time}.png")
        with open(qr_img_path, "wb") as f:
            f.write(img_bytes)

        return qr_img_path

    @staticmethod
    def _wait_for_login(page, max_wait=60, interval=3):
        """轮询等待用户扫码登录"""
        num = 0
        while num < max_wait:
            if page.query_selector("span:has-text('发布笔记')"):
                return
            time.sleep(interval)
            send_message.send_message_to_telegram('请尽快扫码登录小红书！')
            num += interval
        logger.error("登录超时，二维码未被扫描！")
        raise Exception("登录超时，二维码未被扫描！")

    def _save_cookie(self, context):
        """保存 cookie 到数据库"""
        cookie = context.storage_state()
        data = {
            "platform_type": self.platform_type,
            "account_id": cookie.get('account_id', ''),
            "nickname": cookie.get('nickname', ''),
            "password": cookie.get('password', ''),
            "phone": cookie.get('phone', ''),
            "email": cookie.get('email', ''),
            "cookie": cookie,
            "expiration_time": cookie.get('expiration_time', 0)
        }
        Account.objects.create(**data)
