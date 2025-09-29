import json
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from django.contrib.auth.models import User, AnonymousUser
from asgiref.sync import sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from .models import AuditLog, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # достаём токен из query ?token=...
        query_string = parse_qs(self.scope["query_string"].decode())
        raw_token = query_string.get("token", [None])[0]

        if not raw_token:
            await self.close()
            return

        try:
            access_token = AccessToken(raw_token)
            user_id = access_token["user_id"]
            self.user = await sync_to_async(User.objects.get)(id=user_id)
            self.scope["user"] = self.user
        except Exception as e:
            print("JWT error:", e)
            self.scope["user"] = AnonymousUser()
            await self.close()
            return

        # создаём группу для сообщений этого пользователя
        self.room_group_name = f"user_{self.user.username}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await sync_to_async(AuditLog.objects.create)(
            user=self.user,
            action="Connected to WebSocket",
            timestamp=timezone.now()
        )

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        if hasattr(self, "user") and not self.user.is_anonymous:
            await sync_to_async(AuditLog.objects.create)(
                user=self.user,
                action="Disconnected from WebSocket",
                timestamp=timezone.now()
            )

    async def receive(self, text_data):
        if not hasattr(self, "user") or self.user.is_anonymous:
            await self.close()
            return

        try:
            data = json.loads(text_data)
            receiver_username = data.get("receiver")
            content = data.get("content")
        except Exception:
            return

        # проверяем получателя
        receiver_exists = await sync_to_async(User.objects.filter(username=receiver_username).exists)()
        if not receiver_exists:
            await self.send(text_data=json.dumps({"error": "Receiver not found"}))
            return

        # отправляем в группу получателя
        await self.channel_layer.group_send(
            f"user_{receiver_username}",
            {
                "type": "chat_message",
                "message": content,
                "sender": self.user.username,
            }
        )

        try:
            receiver = await sync_to_async(User.objects.get)(username=receiver_username)
            await sync_to_async(Message.objects.create)(
                sender=self.user,
                receiver=receiver,
                content=content,
            )
            await sync_to_async(AuditLog.objects.create)(
                user=self.user,
                action=f"Sent message to {receiver_username} via WS",
                timestamp=timezone.now()
            )
        except User.DoesNotExist:
            pass

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender": event["sender"],
        }))