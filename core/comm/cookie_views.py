import logging
from rest_framework.decorators import action
from rest_framework.response import Response
from core.comm.base_views import BaseViewSet
from .task import generate_xiaohongshu_cookie
import json
import os
from django_celery_beat.models import PeriodicTask, IntervalSchedule


logger = logging.getLogger(__name__)


class CookieViewSet(BaseViewSet):

    @action(detail=False, methods=['post'])
    def generate_xhs_cookie(self, request):
        nickname = request.data.get('nickname', None)
        generate_xiaohongshu_cookie.delay(nickname)
        return Response("后台执行中~")

    @action(detail=False, methods=['post'])
    def toggle_task(self, request, *args, **kwargs):
        task_name = request.data.get(
            "task_name", "core.comm.task.check_and_refresh_cookies"
        )
        interval_hours = request.data.get("interval_hours", os.getenv('COOKIE_INTERVAL_HOURS', 12))
        enabled = str(request.data.get("enabled", "false")).lower() in ("true", "1", "yes")

        if task_name is None:
            return Response({"error": "缺少参数 task_name"})

        try:
            # 创建或获取 IntervalSchedule
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=int(interval_hours),
                period=IntervalSchedule.HOURS
            )

            # 获取或创建 PeriodicTask
            task, created = PeriodicTask.objects.get_or_create(
                task=task_name,
                defaults={
                    "name": f"{task_name}_periodic",
                    "interval": schedule,
                    "enabled": enabled,
                    "args": json.dumps([]),
                }
            )

            if not created:
                task.enabled = enabled
                task.interval = schedule
                task.save()

            return Response({
                "message": f"任务 {task_name} {'已启动' if enabled else '已停止'}",
                "enabled": task.enabled,
                "interval_hours": schedule.every
            })

        except Exception as e:
            return Response({"error": str(e)})
