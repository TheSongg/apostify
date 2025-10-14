import asyncio
import os
import logging
from playwright.async_api import async_playwright


logger = logging.getLogger("app")
_browser = None
_playwright_instance = None
_ws_url = f"ws://playwright:{os.getenv('PLAYWRIGHT_PORT')}"

async def _init_browser():
    global _browser, _playwright_instance
    if _browser:
        return _browser

    _playwright_instance = await async_playwright().start()
    _browser = await _playwright_instance.chromium.connect_over_cdp(_ws_url)
    logger.info(f"初始化：已连接到browser：{_ws_url}")
    return _browser

def get_event_loop():
    """获取同步环境的 asyncio loop"""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

def get_browser():
    """同步接口，返回全局 browser"""
    loop = get_event_loop()
    return loop.run_until_complete(_init_browser())
