from .models import Account, Videos
from rest_framework import serializers


class AccountSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)


    class Meta:
        model = Account
        fields = "__all__"


class VideosSerializer(serializers.ModelSerializer):
    upload_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)


    class Meta:
        model = Videos
        fields = "__all__"