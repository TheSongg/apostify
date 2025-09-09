import logging
from playwright.async_api import async_playwright
from core.comm import send_message
import os
from utils.comm import init_browser, save_qr, update_account, query_expiration_time
import json
import asyncio
from core.comm.serializers import AccountSerializer
from utils.static import PlatFormType
from utils.config import SHIPINHAO_HOME, SHIPINHAO_USER_INFO


logger = logging.getLogger(__name__)


async def async_generate_shipinhao_cookie(nickname):
    try:
        async with async_playwright() as playwright:
            # 初始化浏览器
            browser, context, page = await init_browser(playwright)

            # 打开主页
            await page.goto(SHIPINHAO_HOME)

            # 生成二维码
            src = await _generate_qr(page)
            qr_img_path = await save_qr(src, 'shipinhao')

            # 使用 Telegram 机器人发送图片
            if os.getenv('USE_TELEGRAM_BOT') in ['True', True]:
                await send_message.send_img_to_telegram(qr_img_path, '请扫描二维码登陆视频号！')

            # 等待扫码登录
            auth_data_list = await _wait_for_login(page)

            # 保存 cookie
            data = await save_cookie(context, nickname, auth_data_list=auth_data_list)

            await context.close()
            await browser.close()
            await update_account(data)
            logger.info("登录二维码保存成功！")
            await send_message.send_message_to_all_bot(f"[{data.get('nickname')}]视频号Cookie更新成功~")

    except Exception as e:
        logger.error(e)
        msg = f"{nickname or ''}视频号Cookie更新失败，错误：{e}"
        await send_message.send_message_to_all_bot(msg)
    finally:
        await asyncio.to_thread(os.remove, qr_img_path)
        

async def _generate_qr(page):
    # 等待二维码加载

    # 定位 iframe，二维码不在page中
    frame = page.frame_locator("iframe.display")

    # 在 iframe 内查找二维码
    qrcode_img = frame.locator("img.qrcode")
    await qrcode_img.wait_for()

    src = await qrcode_img.get_attribute("src")
    if not (src and src.startswith("data:image")):
        logger.error("未找到登录二维码！")
        raise Exception("未找到登录二维码！")

    return src


async def _wait_for_login(
        page,
        max_wait=int(os.getenv('COOKIE_MAX_WAIT', 180)),
        interval=1,
        max_retry=int(os.getenv('MAX_RETRIES', 3))
):
    """轮询等待用户扫码登录，同时监听 auth_data 接口"""
    auth_data_list = []

    # 定义响应处理函数
    async def handle_response(response):
        if response.url.startswith(SHIPINHAO_USER_INFO):
            try:
                data = await response.json()
                auth_data_list.append(data)
                logger.info("捕获到 auth_data 接口返回数据: %s", data)
            except:
                logger.warning("非 JSON 响应: %s", response.url)

    # 注册响应监听
    page.on("response", lambda response: asyncio.create_task(handle_response(response)))

    for attempt in range(1, max_retry + 1):
        logger.info("第 %d 次等待扫码登录...", attempt)
        num = 0

        while num < max_wait:
            # 查询元素，判断是否登录成功
            login_success = await page.query_selector("span:has-text('发表')")
            if login_success and auth_data_list:
                logger.info("用户已扫码登录且捕获到 auth_data 数据")
                return auth_data_list

            await asyncio.sleep(interval)
            num += interval

        logger.warning("第 %d 次尝试超时，未捕获到 auth_data 数据，重试...", attempt)

    # 如果超过重试次数仍未捕获数据
    logger.error("登录超时或未捕获到 auth_data 数据！")
    raise Exception("登录超时或未捕获到 auth_data 数据")


async def save_cookie(context, nickname=None, instance=None, auth_data_list=list):
    """异存 cookie 到数据库"""
    cookie = await context.storage_state()
    expiration_time = query_expiration_time(cookie)
    if instance is not None:
        data = AccountSerializer(instance=instance).data
        data['expiration_time'] = expiration_time
        data['cookie'] = cookie
    else:
        data = await get_user_profile(auth_data_list, cookie, expiration_time)

    if nickname not in [None, '', 'None']:
        if nickname != data['nickname']:
            raise Exception(f'请使用{nickname}账号扫码登录！')

    return data


async def get_user_profile(auth_data_list, cookie, expiration_time):
    """使用保存的登录态获取用户昵称"""
    for auth_data in auth_data_list:
        finder_user = auth_data.get('data', {}).get('finderUser', {})
        if finder_user:
            data = {
                "platform_type": PlatFormType.shipinhao.value,
                "account_id": finder_user.get('uniqId', ''),
                "nickname": finder_user.get('nickname', ''),
                "password": finder_user.get('password', ''),
                "phone": finder_user.get('mobile', ''),
                "email": finder_user.get('email', ''),
                "cookie": cookie,
                "expiration_time": expiration_time
            }
            return data
    raise Exception("沒有匹配到视频号用户数据！")
