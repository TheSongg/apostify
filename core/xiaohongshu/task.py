from celery import shared_task
import os
from core.comm import send_message
import logging
from core.comm.models import Account
from playwright.async_api import async_playwright
import asyncio
from utils.comm import init_browser, associated_account_and_video, update_account
from .cookie import save_cookie


logger = logging.getLogger(__name__)


@shared_task
def upload_videos(nickname, platform_type, file_path, title, tags, video_name):
    asyncio.run(async_upload_task(nickname, platform_type, file_path, title, tags, video_name))


async def _upload_for_account(playwright, account, file_path, title, tags):
    """为单个账号上传视频"""
    browser, context, page = await init_browser(playwright, account.cookie)

    await page.goto(os.getenv('XHS_VIDEO_PAGE'))
    await page.wait_for_url(os.getenv('XHS_VIDEO_PAGE'))

    await _upload_video_file(page, file_path)
    await asyncio.sleep(0.5)
    await _fill_title(page, title)
    await asyncio.sleep(0.5)
    await _fill_tags(page, tags)
    await asyncio.sleep(0.5)
    await _release_video(page)
    await asyncio.sleep(0.5)

    return browser, context


async def _upload_video_file(page, file_path,
                             max_wait=int(os.getenv('VIDEO_UPLOAD_MAX_WAIT', 60)),
                             interval=1,
                             max_retries=int(os.getenv('MAX_RETRIES'))):
    """
    异步上传视频并等待完成
    """
    for attempt in range(1, max_retries + 1):
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
                except:
                    # 等待期间未完成，继续轮询
                    await asyncio.sleep(interval)
                finally:
                    elapsed += interval

            raise Exception('上传视频超时！')
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"[-] 上传失败，第 {attempt} 次尝试，错误：{e}，准备重试...")
                await asyncio.sleep(2)
            else:
                raise Exception(f"上传视频失败，已重试 {max_retries} 次，错误：{e}")


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


async def _release_video(page):
        # 等待包含"定时发布"文本的button元素出现并点击
        await page.locator('button:has-text("发布")').click()
        await page.wait_for_url(
            os.getenv('XHS_VIDEO_SCHEDULED_RELEASE_PAGE'),
            timeout=int(os.getenv('DEFAULT_TIMEOUT'))
        )  # 如果自动跳转到作品页面，则代表发布成功


async def async_upload_task(nickname, platform_type, file_path, title, tags, video_name):
    error_info = []

    account = await asyncio.to_thread(
        lambda: Account.objects.filter(
            platform_type=platform_type,
            is_available=True,
            nickname=nickname
        ).first()
    )
    try:
        async with async_playwright() as playwright:

            browser, context = await _upload_for_account(playwright, account, file_path, title, tags)
            cookie = await context.storage_state()

            # 发送通知
            if error_info:
                await send_message.send_message_to_all_bot(f'{";".join(error_info)}')
            else:
                await send_message.send_message_to_all_bot(f'[{nickname}]小红书账号发布成功！')

            # 更新数据库，仍然同步
            await asyncio.to_thread(lambda: associated_account_and_video(account, video_name))

            data = await save_cookie(context, instance=account, nickname=nickname)
            await update_account(data)

    except Exception as e:
        logger.error(f'账号 {nickname} 上传失败，错误：{str(e)}')
        error_info.append(f'账号 {nickname} 上传失败，错误：{str(e)}')
    finally:
        try:
            if context and not context._closed:  # 避免重复关闭
                await context.close()
        except Exception as e:
            logger.debug(f"关闭 context 出错: {e}")

        try:
            if browser and not browser._closed:
                await browser.close()
        except Exception as e:
            logger.debug(f"关闭 browser 出错: {e}")