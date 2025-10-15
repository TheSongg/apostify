import asyncio
import aiohttp
from playwright.async_api import async_playwright


_browser = None
_http_url = "http://playwright:9222/json/version"


async def _init_browser():
    global _browser
    if _browser:
        return _browser

    async with aiohttp.ClientSession() as session:
        async with session.get(_http_url) as resp:
            data = await resp.json()
            ws_url = data.get('webSocketDebuggerUrl', '')
            if not ws_url:
                raise Exception('***** ws_url error *****')

    _playwright_instance = await async_playwright().start()
    _browser = await _playwright_instance.chromium.connect_over_cdp(ws_url)
    print(f"_init_browser：connecting browser：{ws_url}")
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