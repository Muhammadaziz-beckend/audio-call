from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Call, ManagerStatus

User = get_user_model()


class ManagerSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "status"]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_status(self, obj):
        ms = getattr(obj, "manager_status", None)
        return ms.status if ms else "offline"


class ManagerStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagerStatus
        fields = ["status"]


class CallSerializer(serializers.ModelSerializer):
    manager_name = serializers.SerializerMethodField()

    class Meta:
        model = Call
        fields = [
            "id",
            "caller_name",
            "caller_phone",
            "manager",
            "manager_name",
            "status",
            "started_at",
            "ended_at",
            "duration",
            "room_id",
        ]
        read_only_fields = ["started_at", "room_id"]

    def get_manager_name(self, obj):
        if obj.manager:
            return obj.manager.get_full_name() or obj.manager.username
        return None


class CallCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Call
        fields = ["caller_name", "caller_phone"]

    def create(self, validated_data):
        import uuid
        validated_data["room_id"] = str(uuid.uuid4())
        return super().create(validated_data)


class CallAssignSerializer(serializers.Serializer):
    manager_id = serializers.IntegerField()

    def validate_manager_id(self, value):
        try:
            user = User.objects.get(pk=value)
            ms = getattr(user, "manager_status", None)
            if not ms or ms.status != "available":
                raise serializers.ValidationError("Менеджер недоступен")
        except User.DoesNotExist:
            raise serializers.ValidationError("Менеджер не найден")
        return value
