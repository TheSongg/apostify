import asyncio
import aiohttp
import socket
from playwright.async_api import async_playwright


_browser = None


async def get_chrome_json_url(container_name="playwright", port=9222):
    """
    异步解析容器名获取 IP，并生成可访问 Chrome DevTools 的 URL
    """
    try:
        ip = await asyncio.to_thread(socket.gethostbyname, container_name)
    except socket.gaierror:
        raise Exception(f"无法解析容器名 {container_name}")

    url = f"http://{ip}:{port}/json/version"
    return url


async def _init_browser():
    global _browser
    if _browser:
        return _browser

    _http_url = await get_chrome_json_url()
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