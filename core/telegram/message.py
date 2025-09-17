import os
import logging
import asyncio
from telegram import Bot


TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TG_Bot = Bot(token=TG_BOT_TOKEN)
logger = logging.getLogger(__name__)


async def send_photo(img_path, caption='', parse_mode='HTML', reply_markup=None):
    with open(img_path, "rb") as f:
        message = await TG_Bot.send_photo(
            chat_id=CHAT_ID,
            photo=f,
            caption=f"{caption}",
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )

    # 60s后删除消息
    await asyncio.sleep(60)
    await TG_Bot.delete_message(chat_id=CHAT_ID, message_id=message.message_id)


async def send_message(text, parse_mode='HTML', reply_markup=None):
    await TG_Bot.send_message(
        chat_id=CHAT_ID,
        text=text,
        parse_mode=parse_mode,
        reply_markup=reply_markup
    )

