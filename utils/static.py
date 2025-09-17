from enum import Enum
import os


PLATFORM_TYPE_CHOICES = {
    1: {'en': 'xiaohongshu', 'zh': '小红书'},
    2: {'en': 'douyin', 'zh': '抖音'},
    3: {'en': 'toutiao', 'zh': '今日头条'},
    4: {'en': 'shipinhao', 'zh': '视频号'},
    5: {'en': 'kuaishou', 'zh': '快手'},
    6: {'en': 'youtube', 'zh': 'YouTube'},
    7: {'en': 'tiktok', 'zh': 'TikTok'},
    8: {'en': 'instagram', 'zh': 'Instagram'},
}

class PlatFormType(Enum):
    xiaohongshu = 1
    douyin = 2
    toutiao = 3
    shipinhao = 4
    kuaishou = 5
    youtube = 6
    tiktok = 7
    instagram = 8
