import logging
from playwright.async_api import async_playwright
from core.comm import send_message
import os
from utils.comm import init_browser, save_qr, update_account, query_expiration_time
import asyncio


logger = logging.getLogger(__name__)


async def async_generate_douyin_cookie(nickname):
    try:
        async with async_playwright() as playwright:
            # 初始化浏览器
            browser, context, page = await init_browser(playwright)

            # 打开主页
            await page.goto(os.getenv('DOUYIN_HOME'))

            # 生成二维码
            src = await _generate_qr(page)
            qr_img_path = await save_qr(src, 'douyin')

            # 使用 Telegram 机器人发送图片
            if os.getenv('USE_TELEGRAM_BOT') in ['True', True]:
                await send_message.send_img_to_telegram(qr_img_path, '请扫描二维码登陆抖音！')

            # 等待扫码登录
            await _wait_for_login(page)

            # 保存 cookie
            data = await _save_cookie(context, nickname)

            await context.close()
            await browser.close()
            await update_account(data)
            logger.info("登录二维码保存成功！")
            await send_message.send_message_to_all_bot(f"[{nickname}]抖音Cookie更新成功~")

    except Exception as e:
        logger.error(e)
        msg = f"{nickname or ''}小红书Cookie更新失败，错误：{e}"
        await send_message.send_message_to_all_bot(msg)
    finally:
        await asyncio.to_thread(os.remove, qr_img_path)


async def _generate_qr(page):
    # 等待二维码加载
    img = page.locator("img.qrcode_img-NPVTJs")
    await asyncio.sleep(1)
    await page.wait_for_selector("img.qrcode_img-NPVTJs")

    # 获取二维码 src
    src = await img.get_attribute("src")
    if not (src and src.startswith("data:image")):
        logger.error("未找到登录二维码！")
        raise Exception("未找到登录二维码！")

    return src

async def _wait_for_login(page, max_wait=60, interval=3):
    """轮询等待用户扫码登录"""
    num = 0
    while num < max_wait:
        # 查询元素
        login_success = await page.query_selector("span:has-text('高清发布')")
        if login_success:
            return

        await asyncio.sleep(interval)
        num += interval

    logger.error("登录超时，二维码未被扫描！")
    raise Exception("登录超时，二维码未被扫描！")


async def _save_cookie(context, nickname=None):
    """异存 cookie 到数据库"""
    cookie = await context.storage_state()
    expiration_time = query_expiration_time(cookie)
    res_data = await get_user_profile(cookie)
    data = query_user_info(cookie, res_data, expiration_time)

    if nickname is not None:
        if nickname != data['nickname']:
            raise Exception(f'请使用{nickname}账号扫码登录！')

    return data


async def get_user_profile(cookie):
    """使用保存的登录态获取用户昵称"""
    try:
        async with async_playwright() as playwright:
            browser, context, page = await init_browser(playwright, cookie)

            # 请求用户信息接口
            response = await page.request.get(os.getenv('DOUYIN_USER_INFO'))
            res_data = await response.json()

            await context.close()
            await browser.close()

        return res_data
    except Exception as e:
        raise Exception(f'查询抖音昵称信息失败， 错误：{str(e)}')


def query_user_info(cookie, res_data, expiration_time):
    user_profile = res_data.get('user_profile', {})
    data = {
        "platform_type": 2,
        "account_id": user_profile.get('unique_id', ''),
        "nickname": user_profile.get('nick_name', ''),
        "password": user_profile.get('password', ''),
        "phone": user_profile.get('mobile', ''),
        "email": user_profile.get('email', ''),
        "cookie": cookie,
        "expiration_time": expiration_time
    }
    return data
