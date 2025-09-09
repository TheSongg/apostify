import os
import sys
import logging
import asyncio
from telegram import Bot
from utils.static import BOT_LIST
from telegram.helpers import escape_markdown


logger = logging.getLogger(__name__)


async def send_img_to_telegram(img_path, msg=''):
    """异步通过 telegram 库发送图片"""
    bot = Bot(token=os.getenv("TG_BOT_TOKEN"))
    chat_id = os.getenv("CHAT_ID")
    with open(img_path, "rb") as f:
        await bot.send_photo(chat_id=chat_id, photo=f, caption=msg)


async def send_message_to_telegram(text):
    """异步通过 Telegram Bot 发送文字"""
    bot = Bot(token=os.getenv("TG_BOT_TOKEN"))
    chat_id = os.getenv("CHAT_ID")
    safe_text = escape_markdown(text, version=2)

    await bot.send_message(
        chat_id=chat_id,
        text=safe_text,
        parse_mode="MarkdownV2"
    )


async def send_message_to_all_bot(text):
    """异步发送消息到所有机器人"""
    tasks = []
    module = sys.modules[__name__]

    for bot in BOT_LIST:
        bot_name = bot.split('_')[1].lower()
        try:
            func = getattr(module, f"send_message_to_{bot_name}")
            tasks.append(func(text))
        except Exception as e:
            logger.error(f'发送消息到机器人 {bot_name} 异常，错误：{str(e)}')

    if tasks:
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for bot, result in zip(BOT_LIST, results):
            if isinstance(result, Exception):
                logger.error(f"{bot} 发送失败: {result}")
