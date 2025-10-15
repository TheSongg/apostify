import asyncio
import aiohttp
import socket
from pathlib import Path
from playwright.async_api import async_playwright

_browser = None
_playwright_instance = None



async def get_browser_async():
    """
    纯异步版本，供异步代码直接 await 使用
    """
    return await init_browser()


def get_browser():
    """
    同步版本：可在非 async 环境下使用。
    若事件循环已在运行，则通过线程执行异步代码。
    """
    try:
        loop = asyncio.get_running_loop()
        # 已经有 loop 运行，转到线程中执行异步调用
        return asyncio.run_coroutine_threadsafe(init_browser(), loop).result()
    except RuntimeError:
        # 当前无正在运行的事件循环 -> 正常创建
        return asyncio.run(init_browser())
