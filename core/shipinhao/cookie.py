import logging
from playwright.async_api import async_playwright
import os
import shutil
from pathlib import Path
from utils.comm import init_browser, save_qr, update_account
import asyncio
from utils.static import PlatFormType
from utils.config import SHIPINHAO_HOME, SHIPINHAO_USER_INFO, SHIPINHAO_UPLOAD_PAGE
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from core.telegram.message import send_photo, delete_message
from core.users.exception import APException


logger = logging.getLogger("shipinhao")


async def generate_cookie(login_phone):
    target_dir = Path(settings.BASE_DIR / "qr_img" / "shipinhao")
    try:
        async with async_playwright() as playwright:
            browser, context, page = await init_browser(playwright)
            await page.goto(SHIPINHAO_HOME)
            src = await _generate_qr(page)
            qr_img_path = await save_qr(src, target_dir, 'shipinhao')

            message = await send_photo(qr_img_path, caption='请扫描二维码登陆视频号！<i>这条消息会在1分钟后删除~</i>')
            auth_data = await _wait_for_login(page)
            data = await get_cookie(context, login_phone, auth_data)

            await context.close()
            await browser.close()
            await update_account(data)
            msg = f"{data['nickname']}视频号账号Cookie更新成功~"
            logger.info(msg)
    except Exception as e:
        raise APException(e)
    finally:
        await asyncio.to_thread(shutil.rmtree, target_dir, ignore_errors=True)
        if message is not None:
            await delete_message(message)


async def _generate_qr(page):
    try:
        # 定位 iframe，二维码不在page中
        frame = page.frame_locator("iframe.display")

        # 在 iframe 内查找二维码
        qrcode_img = frame.locator("img.qrcode")
        await qrcode_img.wait_for()

        src = await qrcode_img.get_attribute("src")
        if not (src and src.startswith("data:image")):
            logger.error("未找到登录二维码！")
            raise APException("未找到登录二维码！")

        return src
    except Exception as e:
        logger.error("获取视频号登录二维码异常！")
        img_bytes = await page.screenshot(full_page=True)
        await send_photo(img_bytes, caption='获取视频号登录二维码异常！')
        raise APException(f"获取视频号登录二维码异常！错误：{e}")


async def _wait_for_login(page):
    try:
        auth_data = await handle_response(page)
        # await page.wait_for_selector("span:has-text('发表')")
        logger.info('登录二维码已被扫描~')
        return auth_data

    except PlaywrightTimeoutError:
        logger.error("登录超时或二维码未被扫描！")
        img_bytes = await page.screenshot(full_page=True)
        await send_photo(img_bytes, caption='登录超时或二维码未被扫描！')
        raise APException("登录超时或二维码未被扫描！")
    except Exception as e:
        raise APException(f"登录异常，错误：{e}")


async def get_cookie(context, login_phone, auth_data):
    cookie = await context.storage_state()
    _data = auth_data.get('data', {})
    finder_user = _data.get('finderUser', {})
    data = {
        "platform_type": PlatFormType.shipinhao.value,
        "account_id": finder_user.get('uniqId', ''),
        "nickname": finder_user.get('nickname', ''),
        "password": finder_user.get('password', ''),
        "phone": login_phone,
        "email": finder_user.get('email', ''),
        "cookie": cookie,
        "is_expired": False
    }
    logger.info(f"{data['nickname']} cookie保存成功")
    return data


async def handle_response(page, max_wait=int(os.getenv("COOKIE_MAX_WAIT", 180))):
    """等待用户扫码登录，同时监听 auth_data 接口"""
    auth_data = {}
    event = asyncio.Event()

    async def listen(response):
        nonlocal auth_data
        if response.url.startswith(SHIPINHAO_USER_INFO):
            try:
                data = await response.json()
                if data.get("data", {}).get("finderUser", {}):
                    auth_data = data
                    logger.info("捕获到 auth_data 接口")
                    event.set()  # 通知主协程
            except Exception:
                logger.warning(f"非 JSON 响应: {response.url}")

    def callback(response):
        asyncio.create_task(listen(response))

    # 注册监听
    page.on("response", callback)

    try:
        await asyncio.wait_for(event.wait(), timeout=max_wait)
        return auth_data
    except Exception as e:
        img_bytes = await page.screenshot(full_page=True)
        await send_photo(img_bytes, caption='捕获到 auth_data 接口异常！')
        raise APException(f"等待用户鉴权信息异常，错误：{e}")
    finally:
        # 移除监听，避免内存泄漏
        try:
            page.remove_listener("response", callback)
        except Exception as e:
            logger.debug(f"移除监听失败: {e}")


async def check_cookie(account):
    try:
        async with async_playwright() as playwright:
            browser, context, page = await init_browser(playwright, account.cookie)
            await page.goto(SHIPINHAO_UPLOAD_PAGE)
            await page.wait_for_selector("span:has-text('发表')")
            logger.info(f"{account.nickname}视频号cookie自动刷新成功！")
    except Exception as e:
        raise APException(f"{account.nickname}视频号cookie更新失败，错误：{e}")