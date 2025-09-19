import logging
from playwright.async_api import async_playwright
import os
from utils.comm import init_browser, save_qr, update_account, query_expiration_time
import asyncio
from core.comm.serializers import AccountSerializer
from utils.static import PlatFormType
from utils.config import SHIPINHAO_HOME, SHIPINHAO_USER_INFO
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from core.telegram.utils import account_list_html_table, account_list_inline_keyboard
from core.telegram.message import send_message, send_photo


logger = logging.getLogger("shipinhao")


async def async_generate_shipinhao_cookie(nickname):
    gen_cookie = True
    msg = 'init'
    try:
        async with async_playwright() as playwright:
            # 初始化浏览器
            browser, context, page = await init_browser(playwright)

            # 打开主页
            await page.goto(SHIPINHAO_HOME)

            # 生成二维码
            src = await _generate_qr(page)
            qr_img_path = await save_qr(src, 'shipinhao')

            await send_photo(qr_img_path, caption='请扫描二维码登陆视频号！<i>这条消息会在1分钟后删除~</i>')

            # 等待扫码登录
            auth_data = await _wait_for_login(page)

            # 保存 cookie
            data = await save_cookie(context, nickname, auth_data=auth_data)

            await context.close()
            await browser.close()
            await update_account(data)
            logger.info("登录二维码保存成功！")
            msg = f"{nickname}视频号账号Cookie更新成功~" if nickname not in [None, '', 'None'] \
                else f"新增{data['nickname']}视频号账号Cookie成功~"
    except Exception as e:
        gen_cookie =False
        logger.error(e)
        msg = f"{nickname}视频号Cookie更新失败，错误：{e}" if nickname not in [None, '', 'None'] \
            else f"新增视频号Cookie失败，错误：{e}"
    finally:
        await send_message(msg)
        await asyncio.to_thread(os.remove, qr_img_path)
        if gen_cookie:
            await send_message(account_list_html_table(), reply_markup=account_list_inline_keyboard())
        

async def _generate_qr(page):
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


async def _wait_for_login(page):
    try:
        auth_data = await handle_response(page)
        # await page.wait_for_selector("span:has-text('发表')")
        logger.info('登录二维码已被扫描~')
        return auth_data

    except PlaywrightTimeoutError:
        logger.error("登录超时或二维码未被扫描！")
        img_bytes = await page.screenshot(full_page=True)
        await send_photo(img_bytes, caption='登录超时或二维码未被扫描！', auto_delete=None)
        raise Exception("登录超时或二维码未被扫描！")
    except Exception as e:
        raise Exception(f"登录异常，错误：{e}")


async def save_cookie(context, nickname=None, instance=None, auth_data=dict):
    """异存 cookie 到数据库"""
    try:
        cookie = await context.storage_state()
        expiration_time = query_expiration_time(cookie)
        if instance is not None:
            data = AccountSerializer(instance=instance).data
            data['expiration_time'] = expiration_time
            data['cookie'] = cookie
        else:
            data = await get_user_profile(auth_data, cookie, expiration_time)

        if nickname not in [None, '', 'None']:
            if nickname != data['nickname']:
                raise Exception(f'请使用{nickname}账号扫码登录！')
        logger.info(f"{data['nickname']} cookie保存成功")
        return data
    except Exception as e:
        raise Exception(f"保存token异常，错误：{e}")


async def get_user_profile(auth_data, cookie, expiration_time):
    """使用保存的登录态获取用户昵称"""
    _data = auth_data.get('data', {})
    finder_user = _data.get('finderUser', {})
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


async def handle_response(page, max_wait=int(os.getenv("COOKIE_MAX_WAIT", 180))):
    """等待用户扫码登录，同时监听 auth_data 接口"""
    auth_data_list = []
    event = asyncio.Event()

    async def listen(response):
        if response.url.startswith(SHIPINHAO_USER_INFO):
            try:
                data = await response.json()
                if data not in auth_data_list:
                    auth_data_list.append(data)
                    logger.info(f"捕获到 auth_data 接口")
                    event.set()  # 通知主协程
            except Exception:
                logger.warning(f"非 JSON 响应: {response.url}")

    def callback(response):
        asyncio.create_task(listen(response))

    # 注册监听
    page.on("response", callback)

    try:
        # 等待事件触发，或超时
        await asyncio.wait_for(event.wait(), timeout=max_wait)
        if not auth_data_list:
            raise Exception("未找到用户鉴权信息！")

        for auth_data in auth_data_list:
            if auth_data.get('data', {}).get('finderUser', {}):
                return auth_data

        logger.error(f"视频号用户鉴权信息{auth_data_list}")
        raise Exception("用户鉴权信息为空或字段变更！")
    except asyncio.TimeoutError:
        raise Exception("等待 auth_data 超时！")
    except Exception as e:
        raise Exception(f"等待用户鉴权信息异常，错误：{e}")
    finally:
        # 移除监听，避免泄漏
        try:
            page.remove_listener("response", callback)
        except Exception as e:
            logger.error(f"移除监听失败: {e}")