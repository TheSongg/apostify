import requests
import os
import sys
import logging


logger = logging.getLogger(__name__)


def send_img_to_telegram(img_path, msg=''):
    """通过 Telegram Bot 发送图片"""
    url = f"https://api.telegram.org/bot{os.getenv('TG_BOT_TOKEN')}/sendPhoto"
    with open(img_path, "rb") as f:
        files = {"photo": f}
        data = {"chat_id": os.getenv('CHAT_ID'), "caption": msg}
        resp = requests.post(url, files=files, data=data)
    if not resp.ok:
        raise Exception('发送图片到 tg bot 失败！')


def send_message_to_telegram(text):
    """通过 Telegram Bot 发送文字"""
    url = f"https://api.telegram.org/bot{os.getenv('TG_BOT_TOKEN')}/sendMessage"
    data = {
        "chat_id": os.getenv('CHAT_ID'),
        "text": text,
        "parse_mode": "Markdown"
    }
    resp = requests.post(url, data=data)
    if not resp.ok:
        raise Exception('发送图片到 tg bot 失败！')



def send_message_to_all_bot(text):
    """发送消息到所有机器人"""
    for bot in BOT_LIST:
        bot_name = bot.split('_')[1].lower()
        try:
            module = sys.modules[__name__]
            func = getattr(module, f"send_message_to_{bot_name}")
            func(text)
        except Exception as e:
            logger.error(f'发送消息到机器人{bot_name}异常， 错误：{str(e)}')


BOT_LIST = [k for k, v in os.environ.items() if k.startswith("USE_") and k.endswith("_BOT") and v in [True, 'True']]
