from celery import shared_task
from utils.comm import set_init_script
import os
from core.comm import send_message
from utils.comm import get_chrome_driver
import logging
from django.db import transaction
from core.comm.models import Videos, Account
from playwright.async_api import async_playwright
import asyncio


logger = logging.getLogger(__name__)


async def _upload_for_account(browser, account, file_path, title, tags):
    """为单个账号上传视频"""
    context = await browser.new_context(storage_state=account.cookie)
    context = await set_init_script(context)
    page = await context.new_page()
    page.set_default_timeout(int(os.getenv('DEFAULT_TIMEOUT')))
    page.set_default_navigation_timeout(int(os.getenv('DEFAULT_TIMEOUT')))

    await page.goto(os.getenv('XHS_VIDEO_PAGE'))
    await page.wait_for_url(os.getenv('XHS_VIDEO_PAGE'))

    await _upload_video_file(page, file_path)
    await _fill_title(page, title)
    await _fill_tags(page, tags)
    await context.close()


async def _upload_video_file(page, file_path, max_wait=120, interval=1):
    """
    异步上传视频并等待完成
    """
    try:
        # 上传文件
        await page.locator("div[class^='upload-content'] input.upload-input").set_input_files(file_path)

        elapsed = 0
        while elapsed < max_wait:
            try:
                # 等待上传输入框出现
                upload_input = await page.wait_for_selector('input.upload-input', timeout=3000)

                # 查找 preview-new 区域
                preview_new = await upload_input.query_selector(
                    'xpath=following-sibling::div[contains(@class, "preview-new")]'
                )
                if preview_new:
                    stage_elements = await preview_new.query_selector_all('div.stage')
                    for stage in stage_elements:
                        text_content = await page.evaluate('(element) => element.textContent', stage)
                        if '上传成功' in text_content:
                            return  # 上传成功

                await asyncio.sleep(interval)
                elapsed += interval
            except Exception:
                # 等待期间未完成，继续轮询
                await asyncio.sleep(interval)
                elapsed += interval

        raise Exception('上传视频超时！')
    except Exception as e:
        raise Exception(f'上传视频失败，错误：{str(e)}')


async def _fill_title(page, title):
    """异步填写标题"""
    await asyncio.sleep(1)

    title_container = page.locator('div.plugin.title-container').locator('input.d-text')
    count = await title_container.count()
    if count:
        await title_container.fill(title[:30])
    else:
        title_container = page.locator(".notranslate")
        await title_container.click()
        await page.keyboard.press("Backspace")
        await page.keyboard.press("Control+KeyA")
        await page.keyboard.press("Delete")
        await page.keyboard.type(title)
        await page.keyboard.press("Enter")


async def _fill_tags(page, tags):
    """异步填写话题"""
    css_selector = ".ql-editor"
    for tag in tags:
        await page.type(css_selector, f"#{tag}")
        await page.press(css_selector, "Space")


@shared_task
def upload_videos(nickname, platform_type, file_path, title, tags, video_name):
    asyncio.run(async_upload_task(nickname, platform_type, file_path, title, tags, video_name))


async def async_upload_task(nickname, platform_type, file_path, title, tags, video_name):
    error_info = []

    account = await asyncio.to_thread(
        lambda: Account.objects.filter(
            platform_type=platform_type,
            is_available=True,
            nickname=nickname
        ).first()
    )

    async with async_playwright() as playwright:
        browser = await get_chrome_driver(playwright)
        try:
            await _upload_for_account(browser, account, file_path, title, tags)
        except Exception as e:
            logger.error(f'账号 {nickname} 上传失败，错误：{str(e)}')
            error_info.append(f'账号 {nickname} 上传失败，错误：{str(e)}')
        finally:
            await browser.close()

    # 发送通知
    if error_info:
        await asyncio.to_thread(lambda: send_message.send_message_to_all_bot(f'{";".join(error_info)}'))
    else:
        await asyncio.to_thread(lambda: send_message.send_message_to_all_bot('所有小红书账号上传成功！'))

    # 更新数据库，仍然同步
    await asyncio.to_thread(lambda: associated_account_and_video(account, video_name))


def associated_account_and_video(account, video_name):
    with transaction.atomic():
        video_instance = Videos.objects.select_for_update().get(name=video_name)
        video_instance.account.set(account)
