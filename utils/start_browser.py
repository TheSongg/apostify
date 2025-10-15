import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright


USER_DATA_DIR = Path("/app/pw-user-data")


async def clean_old_locks():
    """清理 Playwright / Chromium 遗留锁文件"""
    deleted_files = []
    lock_files = ["SingletonLock", "SingletonSocket", "SingletonCookie"]

    for lock_file in lock_files:
        file_path = USER_DATA_DIR / lock_file
        if file_path.exists():
            try:
                # 使用 asyncio.to_thread 在子线程中执行阻塞的文件操作
                await asyncio.to_thread(file_path.unlink)
                deleted_files.append(file_path)
                print(f"删除锁文件: {file_path}")
            except Exception as e:
                print(f"无法删除锁文件 {file_path}: {e}")

    if deleted_files:
        print(f"共删除 {len(deleted_files)} 个锁文件。")
    else:
        print("没有发现需要删除的锁文件。")


async def main():
    await clean_old_locks()

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=os.getenv("HEADLESS", False),
            args=[
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",  # 防止内存不够崩溃
                "--remote-debugging-port=9221",
                "--remote-debugging-address=0.0.0.0",  # 没有效果
                "--remote-debugging-ip=0.0.0.0"  # 没有效果
            ],
        )

        print("浏览器已启动，访问 http://playwright:9222 获取ws url")

        while True:
            await asyncio.sleep(60)


if __name__ == "__main__":
    print("***即将启动浏览器***")
    asyncio.run(main())
