from .models import Account, Videos
from rest_framework import serializers


class AccountSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)


    class Meta:
        model = Account
        fields = "__all__"

    def to_representation(self, instance):
        res = super().to_representation(instance)
        if self.context.get("view") and self.context["view"].action in ["list_accounts"]:
            if res["platform_type"]:
                res["platform_type"] = {
                    "id": res["platform_type"],
                    "name": Account.PLATFORM_TYPE_CHOICES[res["platform_type"]]["zh"]
                }

        return res

    def get_fields(self):
        fields = super().get_fields()
        default_fields = ["platform_type", "nickname", "expiration_time", "is_available", "cookie", "phone",
                          "account_id"]
        if "view" in self.context and "request" in self.context:
            if self.context.get("view") and self.context["view"].action == "list_accounts":
                default_fields = ["platform_type", "nickname", "expiration_time", "is_available", "account_id"]
        return {field: fields[field] for field in default_fields if field in fields}


class VideosSerializer(serializers.ModelSerializer):
    upload_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)


    class Meta:
        model = Videos
        fields = "__all__"