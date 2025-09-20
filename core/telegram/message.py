import os
import logging
import asyncio
from telegram import Bot
from pathlib import Path


TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
logger = logging.getLogger(__name__)


async def send_photo(img, caption='', parse_mode='HTML', reply_markup=None, auto_delete=60):
    bot = Bot(token=TG_BOT_TOKEN)
    if isinstance(img, (str, Path)) and Path(img).exists():
        photo = open(img, "rb")
    elif isinstance(img, (bytes, bytearray)):
        photo = img
    else:
        raise ValueError("img 必须是有效路径或二进制数据")

    try:
        message = await bot.send_photo(
            chat_id=CHAT_ID,
            photo=photo,
            caption=caption,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
        return message

    finally:
        if isinstance(photo, type(open(__file__))):
            photo.close()

async def send_message(text, parse_mode='HTML', reply_markup=None, auto_delete=60):
    bot = Bot(token=TG_BOT_TOKEN)
    message = await bot.send_message(
        chat_id=CHAT_ID,
        text=text,
        parse_mode=parse_mode,
        reply_markup=reply_markup
    )

    return message


async def delete_message(message_id):
    await bot.delete_message(chat_id=CHAT_ID, message_id=message_id)
