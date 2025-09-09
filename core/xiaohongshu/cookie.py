import logging
from playwright.async_api import async_playwright
from core.comm import send_message
import os
from utils.comm import init_browser, save_qr, update_account, query_expiration_time
import json
import asyncio
from core.comm.serializers import AccountSerializer
from utils.static import PlatFormType
from utils.config import XHS_HOME


logger = logging.getLogger(__name__)


async def async_generate_xiaohongshu_cookie(nickname):
    try:
        async with async_playwright() as playwright:
            # 初始化浏览器
            browser, context, page = await init_browser(playwright)

            # 打开主页
            await page.goto(XHS_HOME)

            # 生成二维码
            src = await _generate_qr(page)
            qr_img_path = await save_qr(src, 'xiaohongshu')

            # 使用 Telegram 机器人发送图片
            if os.getenv('USE_TELEGRAM_BOT') in ['True', True]:
                await send_message.send_img_to_telegram(qr_img_path, '请扫描二维码登陆小红书！')

            # 等待扫码登录
            await _wait_for_login(page)

            # 保存 cookie
            data = await save_cookie(context, nickname)

            await context.close()
            await browser.close()
            await update_account(data)
            logger.info("登录二维码保存成功！")
            msg = f"{nickname}小红书账号Cookie更新成功~" if nickname not in [None, '', 'None'] else f"新增{data['nickname']}小红书账号Cookie成功~"
    except Exception as e:
        logger.error(e)
        msg = f"{nickname}小红书Cookie更新失败，错误：{e}" if nickname not in [None, '', 'None'] else f"新增小红书Cookie失败，错误：{e}"
    finally:
        await send_message.send_message_to_all_bot(msg)
        await asyncio.to_thread(os.remove, qr_img_path)


async def _generate_qr(page):
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

    return src


async def _wait_for_login(page, max_wait=int(os.getenv('COOKIE_MAX_WAIT')), interval=1):
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


async def save_cookie(context, nickname=None, instance=None):
    """异存 cookie 到数据库"""
    cookie = await context.storage_state()
    user_info = query_user_info(cookie)
    expiration_time = query_expiration_time(cookie)
    if instance is not None:
        data = AccountSerializer(instance=instance).data
        data['expiration_time'] = expiration_time
        data['cookie'] = cookie
    else:
        data = {
            "platform_type": PlatFormType.xiaohongshu.value,
            "account_id": user_info.get('redId', ''),
            "nickname": user_info.get('userName', ''),
            "password": user_info.get('password', ''),
            "phone": user_info.get('phone', ''),
            "email": user_info.get('email', ''),
            "cookie": cookie,
            "expiration_time": expiration_time
        }
    if nickname not in [None, '', 'None']:
        if nickname != data['nickname']:
            raise Exception(f'请使用{nickname}账号扫码登录！')

    return data


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

