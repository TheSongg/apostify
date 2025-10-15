import logging
from playwright.async_api import async_playwright
import os
from utils.comm import init_page, get_code_instance, update_account, delete_code_instance, save_qr
import json
import asyncio
from pathlib import Path
import shutil
from utils.static import PlatFormType
from utils.config import XIAOHONGSHU_HOME, XIAOHONGSHU_UPLOAD_PAGE
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from core.telegram.message import send_photo, delete_message
from core.users.exception import APException
from django.conf import settings


logger = logging.getLogger("xiaohongshu")


async def generate_cookie(login_phone):
    page = None
    try:
        page = await init_page()
        await page.goto(XIAOHONGSHU_HOME)
        await login_by_mobile(page, login_phone)
        await _wait_for_login(page)
        data = await get_cookie(login_phone)
        await update_account(data)

        msg = f"{login_phone}小红书账号Cookie更新成功~"
        logger.info(msg)
    except Exception as e:
        raise APException(str(e))
    finally:
        if page:
            await page.close()


async def _generate_qr(page, locator="img.css-1lhmg90"):
    """
    :param page:
    :param locator: 默认表示点击生成并扫描二维码登录；否则输入手机号时可能需要再次验证，必须扫描二维码
    :return:
    """

    if locator == "img.css-1lhmg90":
        # 点击登录按钮
        await page.locator("img.css-wemwzq").click()

    # 等待二维码加载
    img = page.locator(locator)
    await page.wait_for_selector(locator)

    # 获取二维码 src
    src = await img.get_attribute("src")
    if not (src and src.startswith("data:image")):
        logger.error("未找到登录二维码！")
        raise APException("未找到登录二维码！")

    return src


async def _wait_for_login(page, max_wait=int(os.getenv('COOKIE_MAX_WAIT', 180))):
    """等待出现 '发布笔记' 按钮"""
    try:
        await page.wait_for_selector(
            "span:has-text('发布笔记')",
            timeout=max_wait * 1000
        )
        logger.info('检测到已登录~')
    except PlaywrightTimeoutError:
        logger.error("登录超时！")
        img_bytes = await page.screenshot(full_page=True)
        await send_photo(img_bytes, caption='登录超时！')
        raise APException("登录超时！")


async def get_cookie(login_phone):
    #  不再获取昵称等信息，太麻烦且没必要
    data = {
        "platform_type": PlatFormType.xiaohongshu.value,
        "account_id": '',
        "nickname": '',
        "password": '',
        "phone": login_phone,
        "email": '',
        "cookie": {},
        "is_expired": False
    }
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
            raise APException('不存在USER_INFO_FOR_BIZ字段！')

        if isinstance(user_info, str):
            user_info = json.loads(user_info)
        return user_info
    except Exception as e:
        raise APException(f'查询user_info异常，错误：{str(e)}')


async def login_by_mobile(page, login_phone):
    try:
        await login(page, login_phone)
    except Exception as e:
        try:
            logger.warning(f'login失败，尝试手动点击登录按钮，错误：{e}')
            # 进入首页后，有可能不会自动弹出登录框，需要手动点击登录按钮
            login_button_ele = await page.wait_for_selector(
                selector="xpath=//*[@id='app']/div[1]/div[2]/div[1]/ul/div[1]/button",
                timeout=5000
            )
            await login_button_ele.click()
            # 弹窗的登录对话框也有两种形态，一种是直接可以看到手机号和验证码的
            # 另一种是需要点击切换到手机登录的
            element = await page.wait_for_selector(
                selector='xpath=//div[@class="login-container"]//div[@class="other-method"]/div[1]',
                timeout=5000
            )
            await element.click()
            await login(page, login_phone)
        except Exception as e:
            logger.warning(f'手动点击手机登录异常...错误:{e}')


async def login(page, login_phone):
    target_dir = Path(settings.BASE_DIR / "qr_img" / "xiaohongshu")
    target_dir.mkdir(parents=True, exist_ok=True)
    message = None
    try:
        login_container = page.locator("div.login-box-container")
        phone_input = login_container.get_by_placeholder("手机号")
        await phone_input.fill(login_phone)

        try:
            await page.wait_for_url("**/web-login**", timeout=10000)
            await page.wait_for_load_state("networkidle")
            qr_code = "img.qrcode-img"
            qr_code_locator = page.locator(qr_code)
            await qr_code_locator.wait_for(state="visible", timeout=5000)
            message = await _handle_qr_code(page, qr_code, target_dir)
            logger.info("重新填充手机号...")
            await phone_input.fill(login_phone)
        except (TimeoutError, PlaywrightTimeoutError) as e:
            logger.info(f'未检测到二次验证二维码，{e}')

        except Exception as e:
            logger.error(f"扫描二次验证二维码异常，错误：{e}")
            raise APException(f"扫描二次验证二维码异常，错误：{e}")
        finally:
            await asyncio.to_thread(shutil.rmtree, target_dir, ignore_errors=True)
            if message is not None:
                await delete_message(message)

        # 删除当前验证码
        await delete_code_instance()
        send_btn = login_container.get_by_text("发送验证码")

        await send_btn.click()
        code_instance = await get_code_instance()

        sms_code_input = login_container.get_by_placeholder("验证码")
        await sms_code_input.fill(code_instance.code)

        # agree_privacy_ele = page.locator("xpath=//div[@class='agreements']//*[local-name()='svg']")
        # await agree_privacy_ele.click()  # 点击同意隐私协议

        submit_btn_ele = page.get_by_role("button", name="登 录")
        await submit_btn_ele.click()
    except Exception as e:
        raise APException(e)


async def _handle_qr_code(page, qr_code, target_dir):
    logger.info("检测到二次验证二维码，开始处理...")
    qr_code_locator = page.locator(qr_code)
    src = await _generate_qr(page, qr_code)
    qr_img_path = await save_qr(src, target_dir, 'xiaohongshu')
    message = await send_photo(
        qr_img_path,
        caption='需要二次验证，请扫描二维码登陆小红书！<i>这条消息会在1分钟后删除~</i>'
    )

    # 等待二维码消失，表示用户已扫描
    await qr_code_locator.wait_for(state="hidden", timeout=60000)
    logger.info("二次验证二维码已扫描。")
    return message


async def check_cookie(account):
    try:
        page = await init_page()
        await page.goto(XIAOHONGSHU_UPLOAD_PAGE)
        await page.wait_for_selector("span:has-text('发布笔记')")
        logger.info(f"{account.phone} cookie未过期！")

    except Exception as e:
        logger.error(f"{account.phone} cookie过期！错误：{str(e)}")
        raise APException(e)
