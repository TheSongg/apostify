from rest_framework import viewsets
import os
import pytz
import re
from .serializers import VideosSerializer
from django.db import transaction
import logging
from rest_framework.response import Response
from django.http import HttpResponse, StreamingHttpResponse
from utils.comm import json_rsp, json_err_rsp
import traceback
from django.conf import settings
from rest_framework.decorators import action
from utils.static import PLATFORM_TYPE_CHOICES
from core.comm.models import VerificationCode


logger = logging.getLogger(__name__)


class BaseViewSet(viewsets.ModelViewSet):

    def db_save(self, serializer, data, instance=None):
        try:
            if instance is None:
                serializer = serializer(data=data, context=self.request.parser_context)
            else:
                serializer = serializer(instance, data=data, context=self.request.parser_context, partial=True)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            return instance
        except Exception as e:
            logger.error(traceback.format_exc())
            raise Exception(f"数据异常！{e}")


    def dispatch(self, request, *args, **kwargs):
        """
        `.dispatch()` is pretty much the same as Django's regular dispatch,
        but with extra hooks for startup, finalize, and exception handling.
        """
        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers  # deprecate?

        try:
            self.initial(request, *args, **kwargs)

            # Get the appropriate handler method
            if request.method.lower() in self.http_method_names:
                handler = getattr(self, request.method.lower(),
                                  self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed

            rsp = handler(request, *args, **kwargs)

            if isinstance(rsp, Response) or isinstance(rsp, HttpResponse) \
                    or isinstance(rsp, StreamingHttpResponse):
                # 视图直接返回为Response对象，不作处理，走渲染器封装
                response = rsp
            else:
                # 视图直接返回数据，用json封装，不走渲染器
                response = json_rsp(rsp)

        except Exception as exc:
            if settings.DEBUG:  # Debug 模式下，抛出异常html
                response = self.handle_exception(exc)
            else:
                response = json_err_rsp(exc)
                if response.status_code == 401:
                    logger.debug(traceback.format_exc())
                    logger.error(exc)
                else:
                    logger.error(traceback.format_exc())

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response


    @action(methods=['post'], detail=False)
    def save_videos(self, request, *args, **kwargs):
        video_file = request.FILES.get("video")
        if not video_file:
            raise Exception("接口中没有待保存的视频文件！")

        try:
            with transaction.atomic():
                instance = self.db_save(VideosSerializer, {})

                now = instance.upload_time.astimezone(pytz.timezone(settings.TIME_ZONE))
                now_str = now.strftime("%Y%m%d%H%M%S")
                month_dir_str = now.strftime("%Y-%m")

                ext = os.path.splitext(video_file.name)[1] or ".mp4"
                video_name = f"{os.path.splitext(video_file.name)[0]}_{now_str}{ext}"
                save_dir_path = os.path.join(settings.BASE_DIR, "videos", month_dir_str)
                os.makedirs(save_dir_path, exist_ok=True)
                save_path = os.path.join(save_dir_path, video_name)

                # 保存文件
                with open(save_path, "wb+") as destination:
                    for chunk in video_file.chunks():
                        destination.write(chunk)

                self.db_save(VideosSerializer, {'name': video_name}, instance)
        except Exception as e:
            transaction.set_rollback(True)
            raise Exception(f"保存视频失败，错误：{str(e)}")

        return Response({"status": "success", "video_name": video_name})

    @action(detail=False, methods=['get'])
    def test(self, request, *args, **kwargs):
        print(request.data)
        return Response({'status':'success'})


    @action(detail=False, methods=['get'])
    def support_platform(self, request, *args, **kwargs):
        return Response(PLATFORM_TYPE_CHOICES)


    @action(detail=False, methods=['post'])
    def fill_in_code(self, request):
        code = request.data.get("code", "")
        old_instances = VerificationCode.objects.all()
        if old_instances:
            for instance in old_instances:
                instance.delete()
        VerificationCode.objects.create(code=code.strip())
        return Response({"status": "success"})


    @action(detail=False, methods=['get'])
    def fill_code(self, request, *args, **kwargs):
        text = self.request.GET.get('text')
        if not text:
            raise Exception("文本不能为空！")

        pattern = r"\b(\d{6}|\d{4})\b"
        matches = re.findall(pattern, text)
        if not matches:
            raise Exception("文本内容异常，未检测到验证码！")

        old_instances = VerificationCode.objects.all()
        if old_instances:
            for instance in old_instances:
                instance.delete()
        VerificationCode.objects.create(code=str(matches[0]).strip())
        return Response({"status": "success"})