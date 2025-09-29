from celery import shared_task
import os
from core.telegram.message import send_message
import logging
from core.comm.models import Account
from playwright.async_api import async_playwright
import asyncio
from utils.comm import init_browser, associated_account_and_video, update_account, close_browser_context
from .cookie import get_cookie, handle_response
from utils.config import SHIPINHAO_UPLOAD_PAGE, SHIPINHAO_UPLOAD_SUCCESS_PAGE


logger = logging.getLogger("shipinhao")


@shared_task
def upload_videos(nickname, platform_type, file_path, title, tags, video_name, category):
    asyncio.run(async_upload_task(nickname, platform_type, file_path, title, tags, video_name, category))


async def _upload_for_account(playwright, account, file_path, title, tags, category):
    """为单个账号上传视频"""
    browser, context, page = await init_browser(playwright, account.cookie)

    auth_data = await handle_response(page)

    await page.goto(SHIPINHAO_UPLOAD_PAGE)
    await page.wait_for_url(SHIPINHAO_UPLOAD_PAGE)

    await _upload_video_file(page, file_path)
    await asyncio.sleep(0.5)
    await _fill_title(page, title)
    await asyncio.sleep(0.5)
    await _fill_tags(page, tags)
    await asyncio.sleep(0.5)
    await add_collection(page)
    await asyncio.sleep(0.5)
    await add_original(page, category)
    await asyncio.sleep(0.5)
    await detect_upload_status(page)
    await asyncio.sleep(0.5)
    await _release_video(page)
    await asyncio.sleep(0.5)

    return browser, context, auth_data


async def _upload_video_file(page, file_path,
                             interval=1,
                             max_retries=int(os.getenv('MAX_RETRIES'))):
    """
    异步上传视频并等待完成
    """
    for attempt in range(1, max_retries + 1):
        try:
            file_input = page.locator('input[type="file"]')
            await file_input.set_input_files(file_path)
            await asyncio.sleep(interval)
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"[-] 上传失败，第 {attempt} 次尝试，错误：{e}，准备重试...")
                await asyncio.sleep(2)
            else:
                raise Exception(f"上传视频失败，已重试 {max_retries} 次，错误：{e}")


async def _fill_title(page, title):
    """异步填写标题"""
    short_title_element = page.get_by_text("短标题", exact=True).locator("..").locator(
        "xpath=following-sibling::div").locator(
        'span input[type="text"]')
    if await short_title_element.count():
        short_title = format_str_for_short_title(title)
        await short_title_element.fill(short_title)


async def _fill_tags(page, tags):
    for index, tag in enumerate(tags, start=1):
        await page.keyboard.type("#" + tag)
        await page.keyboard.press("Space")


async def add_collection(page):
    collection_elements = page.get_by_text("添加到合集").locator("xpath=following-sibling::div").locator(
        '.option-list-wrap > div')
    if await collection_elements.count() > 1:
        await page.get_by_text("添加到合集").locator("xpath=following-sibling::div").click()
        await collection_elements.first.click()


async def add_original(page, category):
    if await page.get_by_label("视频为原创").count():
        await page.get_by_label("视频为原创").check()

    label_locator = await page.locator('label:has-text("我已阅读并同意 《视频号原创声明使用条款》")').is_visible()
    if label_locator:
        await page.get_by_label("我已阅读并同意 《视频号原创声明使用条款》").check()
        await page.get_by_role("button", name="声明原创").click()

    if await page.locator('div.label span:has-text("声明原创")').count() and category:

        if not await page.locator('div.declare-original-checkbox input.ant-checkbox-input').is_disabled():
            await page.locator('div.declare-original-checkbox input.ant-checkbox-input').click()
            if not await page.locator(
                    'div.declare-original-dialog label.ant-checkbox-wrapper.ant-checkbox-wrapper-checked:visible').count():
                await page.locator('div.declare-original-dialog input.ant-checkbox-input:visible').click()
        if await page.locator('div.original-type-form > div.form-label:has-text("原创类型"):visible').count():
            await page.locator('div.form-content:visible').click()
            await page.locator(
                f'div.form-content:visible ul.weui-desktop-dropdown__list li.weui-desktop-dropdown__list-ele:has-text("{category}")').first.click()
            await page.wait_for_timeout(1000)
        if await page.locator('button:has-text("声明原创"):visible').count():
            await page.locator('button:has-text("声明原创"):visible').click()


async def detect_upload_status(page,
                               max_retries=int(os.getenv('MAX_RETRIES'))
                               ):
    for attempt in range(1, max_retries + 1):
        try:
            if "weui-desktop-btn_disabled" not in await page.get_by_role("button", name="发表").get_attribute(
                    'class'):
                logger.info("视频上传完毕")
                break
            else:
                logger.info("正在上传视频中...")
                await asyncio.sleep(2)
                if await page.locator('div.status-msg.error').count() and await page.locator(
                        'div.media-status-content div.tag-inner:has-text("删除")').count():
                    logger.error("发现上传出错了，准备重试！")
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"[-] 上传失败，第 {attempt} 次尝试，错误：{e}，准备重试...")
                await asyncio.sleep(2)
            else:
                raise Exception(f"上传视频失败，已重试 {max_retries} 次，错误：{e}")


async def _release_video(page):
    publish_buttion = page.locator('div.form-btns button:has-text("发表")')
    if await publish_buttion.count():
        await publish_buttion.click()
    await page.wait_for_url(SHIPINHAO_UPLOAD_SUCCESS_PAGE)
    logger.info("  [-]视频发布成功")


async def async_upload_task(nickname, platform_type, file_path, title, tags, video_name, category):
    error_info = ''

    account = await asyncio.to_thread(
        lambda: Account.objects.filter(
            platform_type=platform_type,
            is_available=True,
            nickname=nickname
        ).first()
    )
    try:
        async with async_playwright() as playwright:

            browser, context, auth_data = await _upload_for_account(playwright,
                                                                         account, file_path,
                                                                         title, tags, category)

            # 更新数据库，仍然同步
            await asyncio.to_thread(lambda: associated_account_and_video(account, video_name))

            data = await get_cookie(context, account.phone, auth_data)
            await update_account(data)

    except Exception as e:
        error_info = f'账号 {nickname} 上传失败，错误：{str(e)}'
        raise Exception(error_info)
    finally:
        await close_browser_context(browser, context)

        if not error_info:
            await send_message(f'[{nickname}]抖音账号发布成功！')
        else:
            await send_message(error_info)

def format_str_for_short_title(origin_title: str) -> str:
    # 定义允许的特殊字符
    allowed_special_chars = "《》“”:+?%°"

    # 移除不允许的特殊字符
    filtered_chars = [char if char.isalnum() or char in allowed_special_chars else ' ' if char == ',' else '' for
                      char in origin_title]
    formatted_string = ''.join(filtered_chars)

    # 调整字符串长度
    if len(formatted_string) > 16:
        # 截断字符串
        formatted_string = formatted_string[:16]
    elif len(formatted_string) < 6:
        # 使用空格来填充字符串
        formatted_string += ' ' * (6 - len(formatted_string))

    return formatted_string