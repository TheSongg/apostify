from .models import Account, Videos
from rest_framework import serializers
from utils.static import PLATFORM_TYPE_CHOICES
from datetime import datetime, timezone, timedelta
from django_celery_beat.models import PeriodicTask
from django.utils import timezone


class AccountSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    update_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)


    class Meta:
        model = Account
        fields = "__all__"

    def to_representation(self, instance):
        res = super().to_representation(instance)
        if res['expiration_time']:
            utc_dt = datetime.fromtimestamp(res["expiration_time"], tz=timezone.utc)
            shanghai_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
            res["expiration_time"] = shanghai_dt.strftime("%Y-%m-%d %H:%M:%S")

        if self.context.get("view") and self.context["view"].action in ["list_accounts"]:
            if res["platform_type"]:
                res["platform_type"] = {
                    "id": res["platform_type"],
                    "name": PLATFORM_TYPE_CHOICES[res["platform_type"]]["zh"]
                }

        if self.context.get("view") and self.context["view"].action in ["account_detail"]:
            res["platform_type"] = PLATFORM_TYPE_CHOICES[res["platform_type"]]["zh"]

        return res

    def get_fields(self):
        fields = super().get_fields()
        default_fields = ["id", "platform_type", "nickname", "expiration_time", "is_available", "cookie", "phone",
                          "account_id", "verification_code", "create_time", "update_time", "email"]

        if "view" in self.context and "request" in self.context:
            if self.context.get("view") and self.context["view"].action == "list_accounts":
                default_fields = ["id", "platform_type", "nickname", "expiration_time", "is_available"]

            if self.context.get("view") and self.context["view"].action == "account_detail":
                default_fields = ["id", "platform_type", "nickname", "expiration_time", "is_available",
                                  "phone", "account_id", "create_time", "update_time", "email"]
        return {field: fields[field] for field in default_fields if field in fields}


class VideosSerializer(serializers.ModelSerializer):
    upload_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)


    class Meta:
        model = Videos
        fields = "__all__"


class PeriodicTaskSerializer(serializers.ModelSerializer):
    schedule_description = serializers.SerializerMethodField()
    next_run = serializers.SerializerMethodField()

    class Meta:
        model = PeriodicTask
        fields = "__all__"


    @staticmethod
    def get_schedule_description(obj):
        """根据关联的 schedule 类型返回描述字符串"""
        if obj.interval:
            return f"每 {obj.interval.every} {obj.interval.get_period_display()}"
        elif obj.crontab:
            return str(obj.crontab)
        elif obj.solarschedule:
            return f"日出/日落事件: {obj.solarschedule.event} @ {obj.solarschedule.latitude}, {obj.solarschedule.longitude}"
        elif obj.clocked:
            return f"一次性执行 @ {obj.clocked.clocked_time.isoformat()}"
        return "未知频率"

    @staticmethod
    def get_next_run(obj):
        """返回格式化的下次执行时间，如果 next_run_time 为空则返回 None"""
        if obj.next_run_time:
            return timezone.localtime(obj.next_run_time).strftime('%Y-%m-%d %H:%M:%S %Z')
        return None

    def get_fields(self):
        fields = super().get_fields()
        default_fields = ["id", "name", "enabled", "last_run_at", "total_run_count"]

        if "view" in self.context and "request" in self.context:
            if self.context.get("view") and self.context["view"].action == "list_task":
                default_fields = ["id", "name", "enabled", "last_run_at", "total_run_count"]

        return {field: fields[field] for field in default_fields if field in fields}