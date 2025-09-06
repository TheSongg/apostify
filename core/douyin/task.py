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

            # 发送通知
            if error_info:
                await send_message.send_message_to_all_bot(f'{";".join(error_info)}')
            else:
                await send_message.send_message_to_all_bot(f'[{nickname}]抖音账号发布成功！')

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


async def _upload_for_account(playwright, account, file_path, title, tags):
    """为单个账号上传视频"""
    browser, context, page = await init_browser(playwright, account.cookie)

    await page.goto(os.getenv('DOUYIN_UPLOAD_PAGE'))
    await page.wait_for_url(os.getenv('DOUYIN_UPLOAD_PAGE'))

    await _upload_file(page, file_path)
    await asyncio.sleep(0.5)
    await _fill_title_and_tags(page, title, tags)
    await asyncio.sleep(0.5)
    await _toggle_third_party(page)
    await asyncio.sleep(0.5)
    await _publish_video(page)
    return browser, context


async def _upload_file(page, file_path,
                       max_wait=int(os.getenv('VIDEO_UPLOAD_MAX_WAIT', 60)),
                       interval=1,
                       max_retries=int(os.getenv('MAX_RETRIES'))):
    """选择文件上传并等待跳转到发布页面，支持失败后重试"""
    for attempt in range(1, max_retries + 1):
        try:
            # 设置文件
            await page.locator("div[class^='container'] input").set_input_files(file_path)

            elapsed = 0
            while elapsed < max_wait:
                try:
                    await page.wait_for_url(
                        os.getenv('DOUYIN_UPLOAD_SUCCESS_PAGE_1'),
                        timeout=int(os.getenv('DEFAULT_TIMEOUT', 3000))
                    )
                    return
                except:
                    try:
                        await page.wait_for_url(
                            os.getenv('DOUYIN_UPLOAD_SUCCESS_PAGE_2'),
                            timeout=int(os.getenv('DEFAULT_TIMEOUT', 3000))
                        )
                        return
                    except:
                        await asyncio.sleep(interval)
                finally:
                    elapsed += interval

            raise TimeoutError("上传视频超时！")

        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"[-] 上传失败，第 {attempt} 次尝试，错误：{e}，准备重试...")
                await asyncio.sleep(2)
            else:
                raise Exception(f"上传视频失败，已重试 {max_retries} 次，错误：{e}")


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


async def _publish_video(page, max_wait=int(os.getenv('VIDEO_UPLOAD_MAX_WAIT')), interval=1):
    """点击发布并确认发布成功"""
    elapsed = 0
    while elapsed < max_wait:
        try:
            publish_button = page.get_by_role("button", name="发布", exact=True)
            if await publish_button.count():
                await publish_button.click()
            await page.wait_for_url(os.getenv('DOUYIN_MANAGE_PAGE'), timeout=os.getenv('DEFAULT_TIMEOUT'))
            return
        except:
            await asyncio.sleep(interval)
        finally:
            elapsed += interval