from rest_framework import viewsets
import os
import json
import time
import logging
from rest_framework.response import Response
from django.http import HttpResponse, StreamingHttpResponse
from .comm import json_rsp, json_err_rsp
import traceback
from django.conf import settings


logger = logging.getLogger("app")


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