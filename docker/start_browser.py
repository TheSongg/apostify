import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    debug_port = os.getenv("PLAYWRIGHT_PORT", "9222")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="/app/pw-user-data",
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
    asyncio.run(main())
