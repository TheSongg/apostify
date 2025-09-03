from django.db import models
from django.core.serializers.json import DjangoJSONEncoder


class Account(models.Model):
    PLATFORM_TYPE_CHOICES = {
        1: {'en': 'xiaohongshu', 'zh': '小红书'},
        2: {'en': 'douyin', 'zh': '抖音'},
        3: {'en': 'jinritoutiao', 'zh': '今日头条'},
        4: {'en': 'shipinhao', 'zh': '视频号'},
        5: {'en': 'kuaishou', 'zh': '快手'},
        6: {'en': 'youtube', 'zh': 'YouTube'},
        7: {'en': 'tiktok', 'zh': 'TikTok'},
        8: {'en': 'instagram', 'zh': 'Instagram'},
    }
    platform_type = models.IntegerField(
        null=False, blank=False,
        choices=[(key, value['zh']) for key, value in PLATFORM_TYPE_CHOICES.items()]
    )
    account_id = models.CharField(max_length=100, null=True, blank=True)
    nickname = models.CharField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=500, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.CharField(max_length=50, null=True, blank=True)
    cookie = models.JSONField(default=list, encoder=DjangoJSONEncoder)
    expiration_time = models.IntegerField(default=0, null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    is_available = models.BooleanField(default=True)


class Videos(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    upload_time = models.DateTimeField(auto_now_add=True)
    account = models.ManyToManyField(Account, blank=True, related_name='videos')
