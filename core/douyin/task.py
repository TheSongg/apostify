from celery import shared_task
import os
from core.telegram.message import send_message
import logging
from core.comm.models import Account
from playwright.async_api import async_playwright
import asyncio
from utils.comm import init_browser, associated_account_and_video, update_account, close_browser_context
from .cookie import get_cookie
from utils.config import (DOUYIN_UPLOAD_PAGE, DOUYIN_UPLOAD_SUCCESS_PAGE_1,
                          DOUYIN_UPLOAD_SUCCESS_PAGE_2, DOUYIN_MANAGE_PAGE)
from core.users.exception import APException


logger = logging.getLogger("douyin")


@shared_task
def upload_videos(nickname, platform_type, file_path, title, tags, video_name):
    asyncio.run(async_upload_task(nickname, platform_type, file_path, title, tags, video_name))


async def async_upload_task(nickname, platform_type, file_path, title, tags, video_name):
    text = f'[{nickname}]抖音账号发布成功！'
    account = await asyncio.to_thread(
        lambda: Account.objects.filter(
            platform_type=platform_type,
            is_available=True,
            nickname=nickname
        ).first()
    )
    try:
        async with async_playwright() as playwright:
            browser, context, page = await _upload_for_account(playwright, account, file_path, title, tags)

            # 更新数据库，仍然同步
            await asyncio.to_thread(lambda: associated_account_and_video(account, video_name))

            data = await get_cookie(context, page, account.phone)
            await update_account(data)
    except Exception as e:
        text = f'账号 {nickname} 上传失败，错误：{str(e)}'
        raise APException(text)
    finally:
        await close_browser_context(browser, context)
        await send_message(text)


async def _upload_for_account(playwright, account, file_path, title, tags):
    """为单个账号上传视频"""
    browser, context, page = await init_browser(playwright, account.cookie)

    await page.goto(DOUYIN_UPLOAD_PAGE)
    await page.wait_for_url(DOUYIN_UPLOAD_PAGE)

    await _upload_file(page, file_path)
    await asyncio.sleep(0.5)
    await _fill_title_and_tags(page, title, tags)
    await asyncio.sleep(0.5)
    await _toggle_third_party(page)
    await asyncio.sleep(0.5)
    await _publish_video(page)
    return browser, context, page


async def _upload_file(page, file_path,
                       interval=1,
                       max_retries=int(os.getenv('MAX_RETRIES'))):
    """选择文件上传并等待跳转到发布页面，支持失败后重试"""
    for attempt in range(1, max_retries + 1):
        try:
            # 设置文件
            await page.locator("div[class^='container'] input").set_input_files(file_path)

            try:
                await page.wait_for_url(
                    DOUYIN_UPLOAD_SUCCESS_PAGE_1,
                    timeout=int(os.getenv('DEFAULT_TIMEOUT', 120000))
                )
                return
            except:
                try:
                    await page.wait_for_url(
                        DOUYIN_UPLOAD_SUCCESS_PAGE_2,
                        timeout=int(os.getenv('DEFAULT_TIMEOUT', 120000))
                    )
                    return
                except:
                    await asyncio.sleep(interval)

            raise TimeoutError("上传视频超时！")

        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"[-] 上传失败，第 {attempt} 次尝试，错误：{e}，准备重试...")
                await asyncio.sleep(2)
            else:
                raise APException(f"上传视频失败，已重试 {max_retries} 次，错误：{e}")


async def _fill_title_and_tags(page, title, tags):
    """填充标题和话题"""
    await asyncio.sleep(1)

    title_container = page.get_by_text('作品标题').locator("..").locator("xpath=following-sibling::div[1]").locator("input")
    if await title_container.count():
        await title_container.fill(title)
    else:
        input_box = page.locator(".notranslate")
        await input_box.click()
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Delete")
        await page.keyboard.type(title)
        await page.keyboard.press("Enter")

    css_selector = ".zone-container"
    for tag in tags:
        await page.type(css_selector, "#" + tag)
        await page.press(css_selector, "Space")


async def _toggle_third_party(page):
    """切换同步到头条/西瓜等第三方平台"""
    selector = '[class^="info"] > [class^="first-part"] div div.semi-switch'
    if await page.locator(selector).count():
        if 'semi-switch-checked' not in await page.eval_on_selector(selector, 'div => div.className'):
            await page.locator(selector).locator('input.semi-switch-native-control').click()


async def _publish_video(page, max_retries=int(os.getenv('MAX_RETRIES')), interval=1):
    """点击发布并确认发布成功"""
    for attempt in range(1, max_retries + 1):
        try:
            publish_button = page.get_by_role("button", name="发布", exact=True)
            if await publish_button.count():
                await publish_button.click()
            await page.wait_for_url(DOUYIN_MANAGE_PAGE, timeout=os.getenv('DEFAULT_TIMEOUT', 120000))
            return
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"[-] 上传失败，第 {attempt} 次尝试，错误：{e}，准备重试...")
                await asyncio.sleep(interval)
            else:
                raise APException(f"上传视频失败，已重试 {max_retries} 次，错误：{e}")