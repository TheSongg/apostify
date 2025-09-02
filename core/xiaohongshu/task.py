from celery import shared_task
from utils.comm import set_init_script
import time
import os
from playwright.sync_api import sync_playwright
from core.comm import send_message
import logging


logger = logging.getLogger(__name__)


def _upload_for_account(browser, account, file_path, title, tags):
    """为单个账号上传视频"""
    context = browser.new_context(storage_state=account.cookie)
    context = set_init_script(context)
    page = context.new_page()
    page.goto(os.getenv('XHS_VIDEO_PAGE'))
    page.wait_for_url(os.getenv('XHS_VIDEO_PAGE'))

    _upload_video_file(page, file_path)
    _fill_title(page, title)
    _fill_tags(page, tags)
    context.close()

def _upload_video_file(page, file_path, max_wait=120, interval=1):
    """上传视频并等待完成"""
    page.locator("div[class^='upload-content'] input[class='upload-input']").set_input_files(file_path)

    num = 0
    while num < max_wait:
        try:
            upload_input = page.wait_for_selector('input.upload-input', timeout=3000)
            preview_new = upload_input.query_selector(
                'xpath=following-sibling::div[contains(@class, "preview-new")]'
            )
            if preview_new:
                stage_elements = preview_new.query_selector_all('div.stage')
                for stage in stage_elements:
                    text_content = page.evaluate('(element) => element.textContent', stage)
                    if '上传成功' in text_content:
                        return
            time.sleep(interval)
            num += interval
        except Exception as e:
            raise Exception(f'上传视频失败，错误：{str(e)}')
    raise Exception('上传视频超时！')

def _fill_title(page, title):
    """填写标题"""
    time.sleep(1)
    title_container = page.locator('div.plugin.title-container').locator('input.d-text')
    if title_container.count():
        title_container.fill(title[:30])
    else:
        title_container = page.locator(".notranslate")
        title_container.click()
        page.keyboard.press("Backspace")
        page.keyboard.press("Control+KeyA")
        page.keyboard.press("Delete")
        page.keyboard.type(title)
        page.keyboard.press("Enter")

def _fill_tags(page, tags):
    """填写话题"""
    css_selector = ".ql-editor"
    for tag in tags:
        page.type(css_selector, "#" + tag)
        page.press(css_selector, "Space")


@shared_task
def upload_videos(accounts, file_path, title, tags):
    error_info = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=os.getenv('HEADLESS'), executable_path=os.getenv('CHROME_DRIVER')
        )
        for account in accounts:
            try:
                _upload_for_account(browser, account, file_path, title, tags)
            except Exception as e:
                logger.error(f'账号 {account.nickname} 上传失败， 错误：{str(e)}')
                error_info.append(f'账号 {account.nickname} 上传失败， 错误：{str(e)}')
        browser.close()
    if error_info:
        send_message.send_message_to_all_bot(f'{";".join(error_info)}')
    else:
        send_message.send_message_to_all_bot('所有小红书账号上传成功！')
