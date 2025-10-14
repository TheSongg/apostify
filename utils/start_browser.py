import asyncio
import os
import shutil
from pathlib import Path
from playwright.async_api import async_playwright


USER_DATA_DIR = Path("/app/pw-user-data")


async def clean_old_locks():
    """清理 Playwright / Chromium 遗留锁文件"""
    if not USER_DATA_DIR.exists():
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        print(f"创建 user_data_dir 目录：{USER_DATA_DIR}")
        return

    deleted_files = []
    for pattern in ["LOCK", "SingletonLock"]:
        for file in USER_DATA_DIR.rglob(pattern):
            try:
                file.unlink()
                deleted_files.append(file)
            except Exception as e:
                print(f"无法删除锁文件 {file}: {e}")

    if deleted_files:
        print(f"已清理锁文件: {[f.name for f in deleted_files]}")
    else:
        print("无遗留锁文件")


async def main():
    debug_port = os.getenv("PLAYWRIGHT_PORT", "9222")
    await clean_old_locks()

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=[
                "--no-sandbox",
                f"--remote-debugging-port={debug_port}",
                "--remote-debugging-address=0.0.0.0",
            ],
        )

        print(f"浏览器已启动，可通过 ws://playwright:{debug_port}连接")

        while True:
            await asyncio.sleep(60)


if __name__ == "__main__":
    print(f"***即将启动浏览器***")
    asyncio.run(main())
