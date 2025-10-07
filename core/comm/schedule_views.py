import logging
from rest_framework.decorators import action
from rest_framework.response import Response
from core.comm.base_views import BaseViewSet
import json
import os
from .serializers import PeriodicTaskSerializer
from django_celery_beat.models import PeriodicTask, IntervalSchedule


logger = logging.getLogger("django")


class ScheduleViewSet(BaseViewSet):
    queryset = PeriodicTask.objects.all()
    serializer_class = PeriodicTaskSerializer

    @action(detail=False, methods=['post'])
    def toggle_task(self, request, *args, **kwargs):
        logger.info(f'func:toggle_task, param: {request.data}')
        task_name = request.data.get(
            "task_name", "core.comm.task.refresh_cookies"
        )
        interval_time = request.data.get("interval_time", os.getenv('COOKIE_INTERVAL_TIME', 12))
        enabled = str(request.data.get("enabled", "false")).lower() in ("true", "1", "yes")
        period = request.data.get("period", os.getenv('COOKIE_PERIOD', IntervalSchedule.HOURS))

        if task_name is None:
            return Response({"error": "缺少参数 task_name"})

        try:
            # 创建或获取 IntervalSchedule
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=int(interval_time),
                period=period
            )

            # 获取或创建 PeriodicTask
            task, created = PeriodicTask.objects.get_or_create(
                task=task_name,
                defaults={
                    "name": task_name,
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

    @action(detail=False, methods=['get'])
    def list_task(self, request, *args, **kwargs):
        """
        列出所有定时任务
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = []
        for obj in serializer.data:
            if obj["name"] == "backend_cleanup":
                continue
            data.append(obj)

        return Response(data)
