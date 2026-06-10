import json
from channels.generic.websocket import AsyncWebsocketConsumer


class SignalingConsumer(AsyncWebsocketConsumer):
    """
    WebSocket консьюмер для WebRTC сигнализации.

    Маршруты:
      ws://.../ws/calls/dispatch/      — диспетчер
      ws://.../ws/calls/manager/<id>/  — менеджер
      ws://.../ws/calls/room/<room_id>/— участники комнаты (offer/answer/ICE)
    """

    async def connect(self):
        self.user = self.scope.get("user")
        self.path_type = self.scope["url_route"]["kwargs"].get("type")
        self.room_id = self.scope["url_route"]["kwargs"].get("room_id")
        self.manager_id = self.scope["url_route"]["kwargs"].get("manager_id")

        if self.path_type == "dispatch":
            self.group_name = "dispatchers"

        elif self.path_type == "manager" and self.manager_id:
            self.group_name = f"manager_{self.manager_id}"

        elif self.path_type == "room" and self.room_id:
            self.group_name = f"room_{self.room_id}"

        else:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Получаем сообщение от клиента и рассылаем в группу."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        msg_type = data.get("type")

        # WebRTC сигнализация внутри комнаты
        if msg_type in ("offer", "answer", "ice-candidate") and self.path_type == "room":
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "rtc.signal",
                    "data": data,
                    "sender": self.channel_name,
                },
            )

    # ────────────────────────────────────────────
    # Обработчики событий от channel layer
    # ────────────────────────────────────────────

    async def call_new(self, event):
        """Новый входящий звонок → диспетчеру."""
        await self.send(json.dumps({"type": "call.new", "data": event["data"]}))

    async def call_updated(self, event):
        """Обновление звонка → диспетчеру."""
        await self.send(json.dumps({"type": "call.updated", "data": event["data"]}))

    async def call_incoming(self, event):
        """Звонок назначен → менеджеру."""
        await self.send(json.dumps({"type": "call.incoming", "data": event["data"]}))

    async def call_ended(self, event):
        """Звонок завершён → менеджеру."""
        await self.send(json.dumps({"type": "call.ended", "data": event["data"]}))

    async def manager_status(self, event):
        """Изменение статуса менеджера → диспетчеру."""
        await self.send(json.dumps({"type": "manager.status", "data": event["data"]}))

    async def rtc_signal(self, event):
        """WebRTC offer/answer/ICE — пересылаем всем в комнате кроме отправителя."""
        if event.get("sender") != self.channel_name:
            await self.send(json.dumps(event["data"]))
