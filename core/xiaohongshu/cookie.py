import logging
from playwright.async_api import async_playwright
import os
from utils.comm import init_browser, get_code_instance, update_account, delete_code_instance
import json
import asyncio
from utils.static import PlatFormType
from utils.config import XIAOHONGSHU_HOME, XIAOHONGSHU_UPLOAD_PAGE
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from core.telegram.utils import account_list_html_table, account_list_inline_keyboard
from core.telegram.message import send_message, send_photo, delete_message


logger = logging.getLogger("xiaohongshu")


async def async_generate_xiaohongshu_cookie(login_phone):
    gen_cookie, msg = True, 'init'
    try:
        await generate_cookie(login_phone)
    except Exception as e:
        gen_cookie =False
        msg = f"{login_phone}小红书Cookie更新失败，错误：{e}"
        logger.error(msg)
    finally:
        msg_bot = await send_message(msg)
        if gen_cookie:
            await delete_message(msg_bot)
            await send_message(await account_list_html_table(), reply_markup=account_list_inline_keyboard())


async def generate_cookie(login_phone):
    async with async_playwright() as playwright:
        browser, context, page = await init_browser(playwright)
        await page.goto(XIAOHONGSHU_HOME)
        await login_by_mobile(page, login_phone)
        await _wait_for_login(page)

        data = await get_cookie(context, login_phone)
        await context.close()
        await browser.close()
        await update_account(data)

        msg = f"{data['nickname']}小红书账号Cookie更新成功~"
        logger.info(msg)


async def _generate_qr(page):
    """
    不再使用扫码二维码登录，无法获取手机号，无法自动登录刷新cookie
    :param page:
    :return:
    """
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
        raise Exception("登录超时！")


async def get_cookie(context, login_phone):
    cookie = await context.storage_state()
    user_info = query_user_info(cookie)
    data = {
        "platform_type": PlatFormType.xiaohongshu.value,
        "account_id": user_info.get('redId', ''),
        "nickname": user_info.get('userName', ''),
        "password": user_info.get('password', ''),
        "phone": login_phone,
        "email": user_info.get('email', ''),
        "cookie": cookie,
        "is_expired": False
    }
    logger.info(f"{data['nickname']} cookie保存成功~")
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


async def login_by_mobile(page, login_phone):
    await asyncio.sleep(1)
    try:
        await login(page, login_phone)
    except Exception as e:
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
        logger.warning(f'手动点击手机登录异常...错误:{e}')


async def login(page, login_phone):
    await asyncio.sleep(1)
    login_container = page.locator("div.login-box-container")
    phone_input = login_container.get_by_placeholder("手机号")
    await phone_input.fill(login_phone)
    # 删除当前验证码
    await delete_code_instance()
    send_btn = login_container.get_by_text("发送验证码")

    await send_btn.click()
    code_instance = await get_code_instance()

    sms_code_input = login_container.get_by_placeholder("验证码")
    await sms_code_input.fill(code_instance.code)
    await asyncio.sleep(1)

    # agree_privacy_ele = page.locator("xpath=//div[@class='agreements']//*[local-name()='svg']")
    # await agree_privacy_ele.click()  # 点击同意隐私协议

    submit_btn_ele = page.get_by_role("button", name="登 录")
    await submit_btn_ele.click()


async def check_cookie(account):
    try:
        async with async_playwright() as playwright:
            browser, context, page = await init_browser(playwright, account.cookie)
            await page.goto(XIAOHONGSHU_UPLOAD_PAGE)
            await page.wait_for_selector("span:has-text('发布笔记')")
            logger.info(f"{account.nickname} cookie未过期！")

    except Exception as e:
        logger.error(f"{account.nickname} cookie过期！错误：{str(e)}")
        raise Exception(e)
