import logging
from playwright.async_api import async_playwright
import os
from core.comm.serializers import AccountSerializer
from utils.comm import init_browser, save_qr, update_account, query_expiration_time
import asyncio
from utils.static import PlatFormType
from utils.config import DOUYIN_HOME, DOUYIN_USER_INFO
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from core.telegram.utils import account_list_html_table, account_list_inline_keyboard
from core.telegram.message import send_message, send_photo
from core.comm.models import VerificationCode


logger = logging.getLogger("douyin")


async def async_generate_douyin_cookie(nickname):
    gen_cookie = True
    msg = 'init'
    try:
        async with async_playwright() as playwright:
            # 初始化浏览器
            browser, context, page = await init_browser(playwright)

            # 打开主页
            await page.goto(DOUYIN_HOME)

            # 生成二维码
            src = await _generate_qr(page)
            qr_img_path = await save_qr(src, 'douyin')

            await send_photo(qr_img_path, caption='请扫描二维码登陆抖音！<i>这条消息会在1分钟后删除~</i>')

            # 等待扫码登录
            await _wait_for_login(page)

            # 保存 cookie
            data = await save_cookie(context, nickname, page=page)

            await context.close()
            await browser.close()
            await update_account(data)
            msg = f"{nickname}抖音账号Cookie更新成功~" if nickname not in [None, '','None'] \
                else f"新增{data['nickname']}抖音账号Cookie成功~"
    except Exception as e:
        gen_cookie =False
        msg = f"{nickname}抖音Cookie更新失败，错误：{e}" if nickname not in [None, '', 'None'] \
            else f"新增抖音Cookie失败，错误：{e}"
        logger.error(msg)
    finally:
        await send_message(msg)
        await asyncio.to_thread(os.remove, qr_img_path)
        if gen_cookie:
            await send_message(account_list_html_table(), reply_markup=account_list_inline_keyboard())


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

async def _wait_for_login(page, max_wait=int(os.getenv('COOKIE_MAX_WAIT', 180))):
    """等待用户扫码登录，直到出现 '高清发布' 按钮；如遇验证码，进入验证码处理"""
    code_instance = None
    try:
        # 同时等待两个可能的元素
        result = await page.wait_for_selector(
            "span:has-text('高清发布'), div:has-text('接收短信验证码')",
            timeout=max_wait * 1000
        )

        text = await result.inner_text()

        if "高清发布" in text:
            logger.info("登录成功，二维码已被扫描~")

        elif "接收短信验证码" in text:
            await send_message("检测到需要输入验证码，发送 /code 启动流程")
            logger.warning("扫码成功，但需要短信验证码！")
            await asyncio.sleep(1)
            await page.get_by_text("接收短信验证码").click(force=True)
            code = None
            for i in range(60):
                await asyncio.sleep(1)
                code_instance = VerificationCode.objects.first()
                if code_instance and code_instance.code is not None:
                    code = code_instance.code
                    break
            if code_instance is None or code is None:
                raise Exception("验证码异常或未收到验证码！")

            await asyncio.sleep(1)
            input_box = page.locator("#button-input")
            await input_box.click()
            await input_box.type(code, delay=100)  # 每个字符间隔 100ms

            await asyncio.sleep(1)
            await page.click("button:has-text('验证')")
        else:
            raise Exception("未识别的页面状态！")

    except PlaywrightTimeoutError:
        logger.error("登录超时或二维码未被扫描！")
        img_bytes = await page.screenshot(full_page=True)
        await send_photo(img_bytes, caption="登录超时或二维码未被扫描！", auto_delete=None)
        raise Exception("登录超时或二维码未被扫描！")
    except Exception as e:
        logger.error(f"登录失败，异常：{e}")
        img_bytes = await page.screenshot(full_page=True)
        await send_photo(img_bytes, caption=f"登录失败，异常：{e}", auto_delete=None)
        raise Exception(e)
    finally:
        if code_instance is not None:
            code_instance.delete()


async def save_cookie(context, nickname=None, instance=None, page=None):
    """异存 cookie 到数据库"""
    cookie = await context.storage_state()
    expiration_time = query_expiration_time(cookie)
    if instance is not None:
        data = AccountSerializer(instance=instance).data
        data['expiration_time'] = expiration_time
        data['cookie'] = cookie
    else:
        res_data = await get_user_profile(page)
        data = query_user_info(cookie, res_data, expiration_time)

    if nickname not in [None, '', 'None']:
        if nickname != data['nickname']:
            raise Exception(f'请使用{nickname}账号扫码登录！')
    logger.info(f"{data['nickname']} cookie保存成功")
    return data


async def get_user_profile(page):
    """使用保存的登录态获取用户昵称"""
    try:
        # 请求用户信息接口
        response = await page.request.get(DOUYIN_USER_INFO)
        res_data = await response.json()

        return res_data
    except Exception as e:
        raise Exception(f'查询抖音昵称信息失败， 错误：{str(e)}')


def query_user_info(cookie, res_data, expiration_time):
    user_profile = res_data.get('user_profile', {})
    data = {
        "platform_type": PlatFormType.douyin.value,
        "account_id": user_profile.get('unique_id', ''),
        "nickname": user_profile.get('nick_name', ''),
        "password": user_profile.get('password', ''),
        "phone": user_profile.get('mobile', ''),
        "email": user_profile.get('email', ''),
        "cookie": cookie,
        "expiration_time": expiration_time
    }
    return data
