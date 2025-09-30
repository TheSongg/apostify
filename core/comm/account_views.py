from rest_framework.response import Response
from core.comm.base_views import BaseViewSet
from .models import Account
from .serializers import AccountSerializer
import logging
from rest_framework.decorators import action
from django.db.models import Q
from django.db import transaction
from core.users.exception import APException


logger = logging.getLogger(__name__)


class AccountViewSet(BaseViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


    @action(detail=False, methods=['get'])
    def list_accounts(self, request):
        queryset = self.apply_filters(self.get_queryset(), request.query_params)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @staticmethod
    def apply_filters(queryset, params):
        filter_q = Q()

        # 定义允许过滤的字段
        allowed_filters = ["is_available", "platform_type"]

        # 通用字段过滤
        for key in allowed_filters:
            value = params.get(key)
            if value:
                filter_q &= Q(**{key: value})

        return queryset.filter(filter_q)

    @action(detail=False, methods=['post'])
    def update_account(self, request, *args, **kwargs):
        data = request.data.copy()
        platform_type = data.get('platform_type', None)
        if not platform_type:
            raise APException(f'无效的platform_type：[{platform_type}]')

        phone = data.get('phone')
        email = data.get('email')
        input_data = {
            'phone': phone,
            'email': email,
        }

        filter_q = None

        for field, value in input_data.items():
            if value:
                filter_q = Q(**{field: value})
                break

        if not filter_q:
            raise APException('至少输入一个：[phone，email]')

        instance = self.queryset.filter(
            filter_q,
            platform_type=data.get("platform_type"),
        ).first()
        if not instance:
            raise APException("账号不存在，无法更新！")

        with transaction.atomic():
            updated_instance = self.db_save(self.get_serializer_class(), data, instance)
            self.get_serializer(updated_instance)
        return Response({"status": "success", 'id': updated_instance.id})

    @action(detail=True, methods=['get'])
    def account_detail(self, request, pk=None, *args, **kwargs):
        queryset = self.queryset.filter(id=pk).first()
        if not queryset:
            raise APException(f"不存在该账号:{pk}")

        serializer = self.get_serializer(queryset)
        return Response(serializer.data)
