import logging
from playwright.async_api import async_playwright
import os
import sys
from utils.comm import (init_browser, update_account,
                        get_code_instance, delete_code_instance, get_tracks)
import asyncio
from utils.static import PlatFormType
from utils.config import DOUYIN_HOME, DOUYIN_USER_INFO, DOUYIN_UPLOAD_PAGE
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from core.telegram.message import send_message, send_photo
from asgiref.sync import sync_to_async
from utils.slider import Slider
from core.users.exception import APException


logger = logging.getLogger("douyin")


async def generate_cookie(login_phone):
    async with async_playwright() as playwright:
        browser, context, page = await init_browser(playwright)
        await page.goto(DOUYIN_HOME)
        await login_by_mobile(page, login_phone)

        await _wait_for_login(page)

        # 保存 cookie
        data = await get_cookie(context, page, login_phone)

        await context.close()
        await browser.close()
        await update_account(data)
        msg = f"{data['nickname']}抖音账号Cookie更新成功~"
        logger.info(msg)


async def _generate_qr(page):
    # 等待二维码加载
    img = page.locator("img.qrcode_img-NPVTJs")
    await asyncio.sleep(1)
    await page.wait_for_selector("img.qrcode_img-NPVTJs")

    # 获取二维码 src
    src = await img.get_attribute("src")
    if not (src and src.startswith("data:image")):
        logger.error("未找到登录二维码！")
        raise APException("未找到登录二维码！")

    return src

async def _wait_for_login(page, max_wait=int(os.getenv('COOKIE_MAX_WAIT', 180))):
    """等待用户扫码登录，直到出现 '高清发布' 按钮；如遇验证码，进入验证码处理"""
    code_instance = None
    try:
        task1 = asyncio.create_task(page.wait_for_selector("span:has-text('高清发布')", timeout=max_wait * 1000))
        task2 = asyncio.create_task(page.wait_for_selector("text=接收短信验证码", timeout=max_wait * 1000))

        done, pending = await asyncio.wait(
            [task1, task2],
            return_when=asyncio.FIRST_COMPLETED
        )

        # 获取完成的结果
        result = list(done)[0].result()
        text = await result.inner_text()  # 注意 wait_for_selector 返回的是 ElementHandle，需要 await inner_text()

        # 取消未完成的任务
        for task in pending:
            task.cancel()

        if "高清发布" in text:
            logger.info("登录成功，二维码已被扫描~")

        elif "接收短信验证码" in text:
            logger.warning("扫码成功，但需要短信验证码！")
            await file_in_code(page, max_wait)
        else:
            raise APException("未识别的页面状态！")

    except PlaywrightTimeoutError:
        logger.error("登录超时或二维码未被扫描！")
        img_bytes = await page.screenshot(full_page=True)
        await send_photo(img_bytes, caption="登录超时或二维码未被扫描！")
        raise APException("登录超时或二维码未被扫描！")
    except Exception as e:
        logger.error(f"登录失败，异常：{e}")
        img_bytes = await page.screenshot(full_page=True)
        await send_photo(img_bytes, caption=f"登录失败，异常：{e}")
        raise APException(e)
    finally:
        if code_instance is not None:
            await sync_to_async(code_instance.delete)()

async def file_in_code(page, max_wait):
    await delete_code_instance()
    await send_message("检测到需要输入验证码，发送 /code 启动流程")
    await asyncio.sleep(1)
    await page.get_by_text("接收短信验证码").click(force=True)

    #  获取验证码，由用户从tg bot输入
    code_instance = await get_code_instance()

    await asyncio.sleep(1)
    # 先定位到包含 span 的父容器
    container = page.locator("div:has(span:text('重新发送'))")

    # 再找容器里的 input
    input_box = container.locator("input#button-input")

    # 等待输入框可见
    await input_box.wait_for(state="visible", timeout=max_wait * 1000)

    # 填入验证码
    await input_box.click()
    await input_box.type(code_instance.code, delay=100)  # 每个字符间隔 100ms

    # 找到输入框下方的 div 文本为 “验证”
    verify_button = input_box.locator("xpath=following::div[text()='验证']").first

    # 点击验证按钮
    await verify_button.scroll_into_view_if_needed()
    await verify_button.click(force=True)
    await page.wait_for_selector("span:has-text('高清发布')", timeout=max_wait * 1000)


async def get_cookie(context, page, login_phone):
    """异存 cookie 到数据库"""
    cookie = await context.storage_state()
    res_data = await get_user_profile(page)
    user_profile = res_data.get('user_profile', {})
    data = {
        "platform_type": PlatFormType.douyin.value,
        "account_id": user_profile.get('unique_id', ''),
        "nickname": user_profile.get('nick_name', ''),
        "password": user_profile.get('password', ''),
        "phone": login_phone,
        "email": user_profile.get('email', ''),
        "cookie": cookie,
        "is_expired": False
    }
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
        raise APException(f'查询抖音昵称信息失败， 错误：{str(e)}')


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


async def login_by_mobile(page, login_phone):
    await asyncio.sleep(1)
    mobile_tap_ele = page.locator("xpath=//li[text() = '验证码登录']")
    await mobile_tap_ele.click()
    await page.wait_for_selector("xpath=//article[@class='web-login-mobile-code']")
    mobile_input_ele = page.locator("xpath=//input[@placeholder='手机号']")
    await mobile_input_ele.fill(login_phone)
    await asyncio.sleep(0.5)
    send_sms_code_btn = page.locator("xpath=//span[text() = '获取验证码']")
    await send_sms_code_btn.click()

    # 检查是否有滑动验证码
    await check_page_display_slider(page, move_step=10, slider_level="easy")
    await asyncio.sleep(1)
    # 删除当前验证码
    await delete_code_instance()
    code_instance = await get_code_instance()

    sms_code_input = page.locator("xpath=//input[@placeholder='请输入验证码']")
    await sms_code_input.fill(code_instance.code)
    await asyncio.sleep(1)

#  下面代码参考https://github.com/NanmiCoder/MediaCrawler
async def check_page_display_slider(page, move_step: int = 10, slider_level: str = "easy"):
    """
    检查页面是否出现滑动验证码
    :return:
    """
    # 等待滑动验证码的出现
    back_selector = "#captcha-verify-image"
    try:
        await page.wait_for_selector(selector=back_selector, state="visible", timeout=30 * 1000)
    except PlaywrightTimeoutError:  # 没有滑动验证码，直接返回
        return

    gap_selector = 'xpath=//*[@id="captcha_container"]/div/div[2]/img[2]'
    max_slider_try_times = 20
    slider_verify_success = False
    while not slider_verify_success:
        if max_slider_try_times <= 0:
            sys.exit()
        try:
            await move_slider(back_selector, gap_selector, move_step, slider_level)
            await asyncio.sleep(1)

            # 如果滑块滑动慢了，或者验证失败了，会提示操作过慢，这里点一下刷新按钮
            page_content = await page.content()
            if "操作过慢" in page_content or "提示重新操作" in page_content:
                await page.click(selector="//a[contains(@class, 'secsdk_captcha_refresh')]")
                continue

            # 滑动成功后，等待滑块消失
            await page.wait_for_selector(selector=back_selector, state="hidden", timeout=1000)
            # 如果滑块消失了，说明验证成功了，跳出循环，如果没有消失，说明验证失败了，上面这一行代码会抛出异常被捕获后继续循环滑动验证码
            slider_verify_success = True
        except Exception as e:
            await asyncio.sleep(1)
            max_slider_try_times -= 1
            continue


async def move_slider(page, back_selector: str, gap_selector: str, move_step: int = 10, slider_level="easy"):
    """
    Move the slider to the right to complete the verification
    :param back_selector: 滑动验证码背景图片的选择器
    :param gap_selector:  滑动验证码的滑块选择器
    :param move_step: 是控制单次移动速度的比例是1/10 默认是1 相当于 传入的这个距离不管多远0.1秒钟移动完 越大越慢
    :param slider_level: 滑块难度 easy hard,分别对应手机验证码的滑块和验证码中间的滑块
    :return:
    """

    # get slider background image
    slider_back_elements = await page.wait_for_selector(
        selector=back_selector,
        timeout=1000 * 10,  # wait 10 seconds
    )
    slide_back = str(await slider_back_elements.get_property("src"))  # type: ignore

    # get slider gap image
    gap_elements = await page.wait_for_selector(
        selector=gap_selector,
        timeout=1000 * 10,  # wait 10 seconds
    )
    gap_src = str(await gap_elements.get_property("src"))  # type: ignore

    # 识别滑块位置
    slide_app = Slider(gap=gap_src, bg=slide_back)
    distance = slide_app.discern()

    # 获取移动轨迹
    tracks = get_tracks(distance, slider_level)
    new_1 = tracks[-1] - (sum(tracks) - distance)
    tracks.pop()
    tracks.append(new_1)

    # 根据轨迹拖拽滑块到指定位置
    element = await page.query_selector(gap_selector)
    bounding_box = await element.bounding_box()  # type: ignore

    await page.mouse.move(bounding_box["x"] + bounding_box["width"] / 2,  # type: ignore
                                       bounding_box["y"] + bounding_box["height"] / 2)  # type: ignore
    # 这里获取到x坐标中心点位置
    x = bounding_box["x"] + bounding_box["width"] / 2  # type: ignore
    # 模拟滑动操作
    await element.hover()  # type: ignore
    await page.mouse.down()

    for track in tracks:
        # 循环鼠标按照轨迹移动
        # steps 是控制单次移动速度的比例是1/10 默认是1 相当于 传入的这个距离不管多远0.1秒钟移动完 越大越慢
        await page.mouse.move(x + track, 0, steps=move_step)
        x += track
    await page.mouse.up()


async def check_cookie(account):
    try:
        async with async_playwright() as playwright:
            browser, context, page = await init_browser(playwright, account.cookie)
            await page.goto(DOUYIN_UPLOAD_PAGE)
            data = await get_cookie(context, page, account.phone)

            await context.close()
            await browser.close()
            await update_account(data)
            logger.info(f"{account.nickname}抖音cookie自动刷新成功！")
    except Exception as e:
        raise APException(f"{account.nickname}抖音cookie更新失败，错误：{e}")