from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import ListModelMixin
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Call, ManagerStatus
from .serializers import (
    CallSerializer,
    CallCreateSerializer,
    CallAssignSerializer,
    ManagerSerializer,
    ManagerStatusSerializer,
)

User = get_user_model()


def notify_group(group_name, event_type, data):
    """Отправка события через WebSocket всем в группе."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name,
        {"type": event_type, "data": data},
    )


class CallViewSet(ModelViewSet):
    queryset = Call.objects.select_related("manager").all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CallCreateSerializer
        if self.action == "assign":
            return CallAssignSerializer
        return CallSerializer

    def create(self, request, *args, **kwargs):
        """Входящий звонок — создаём запись и уведомляем диспетчера."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        call = serializer.save(status="waiting")

        # Уведомляем всех диспетчеров о новом звонке
        notify_group(
            "dispatchers",
            "call.new",
            CallSerializer(call).data,
        )

        return Response(CallSerializer(call).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """Назначить менеджера на звонок."""
        call = self.get_object()
        if call.status != "waiting":
            return Response(
                {"detail": "Звонок уже не в ожидании"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CallAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        manager = User.objects.get(pk=serializer.validated_data["manager_id"])
        call.manager = manager
        call.status = "active"
        call.save()

        # Помечаем менеджера как занятого
        ManagerStatus.objects.filter(user=manager).update(status="busy")

        call_data = CallSerializer(call).data

        # Уведомляем менеджера — ему надо принять звонок
        notify_group(f"manager_{manager.id}", "call.incoming", call_data)

        # Уведомляем диспетчеров об обновлении
        notify_group("dispatchers", "call.updated", call_data)

        return Response(call_data)

    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        """Завершить звонок."""
        call = self.get_object()
        call.status = "ended"
        call.ended_at = timezone.now()
        if call.started_at:
            call.duration = int((call.ended_at - call.started_at).total_seconds())
        call.save()

        # Освобождаем менеджера
        if call.manager:
            ManagerStatus.objects.filter(user=call.manager).update(status="available")
            notify_group(f"manager_{call.manager.id}", "call.ended", {"call_id": call.id})

        notify_group("dispatchers", "call.updated", CallSerializer(call).data)

        return Response(CallSerializer(call).data)

    @action(detail=False, methods=["get"])
    def waiting(self, request):
        """Список звонков в ожидании."""
        calls = Call.objects.filter(status="waiting")
        return Response(CallSerializer(calls, many=True).data)


class ManagerViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ManagerSerializer

    def get_queryset(self):
        return User.objects.select_related("manager_status").filter(
            manager_status__isnull=False
        )

    @action(detail=False, methods=["patch"], url_path="my-status")
    def my_status(self, request):
        """Менеджер меняет свой статус (available / busy / offline)."""
        ms, _ = ManagerStatus.objects.get_or_create(user=request.user)
        serializer = ManagerStatusSerializer(ms, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Уведомляем диспетчеров об изменении статуса
        notify_group(
            "dispatchers",
            "manager.status",
            {
                "manager_id": request.user.id,
                "status": ms.status,
            },
        )

        return Response(serializer.data)
