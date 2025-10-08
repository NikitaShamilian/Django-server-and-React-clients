import json, base64
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.contrib.auth.models import User, AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import ed25519

from .models import Message, AuditLog


class ChatConsumer(AsyncWebsocketConsumer):
    """Единый consumer для заданий №1 и №2."""

    async def connect(self):
        """JWT‑аутентификация и подключение."""
        qs = parse_qs(self.scope["query_string"].decode())
        token = qs.get("token", [None])[0]
        if not token:
            await self.close()
            return

        try:
            access = AccessToken(token)
            self.user = await sync_to_async(User.objects.get)(id=access["user_id"])
            self.scope["user"] = self.user
        except Exception as e:
            print("[JWT] ❌", e)
            self.user = AnonymousUser()
            await self.close()
            return

        # защита от двойного коннекта
        if getattr(self, "_connected", False):
            return
        self._connected = True
        self.room_group_name = f"user_{self.user.username}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self._log(f"{self.user.username} connected")
        print(f"[WS] ✅ {self.user.username} connected")

    async def disconnect(self, close_code):
        """Корректное закрытие."""
        if not getattr(self, "_connected", False):
            return
        self._connected = False

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        if hasattr(self, "user") and not self.user.is_anonymous:
            await self._log(f"{self.user.username} disconnected")
            print(f"[WS] 🔌 {self.user.username} disconnected")

    async def receive(self, text_data):
        """Обработка входящих сообщений."""
        if not getattr(self, "user", None) or self.user.is_anonymous:
            await self.close()
            return

        try:
            data = json.loads(text_data)
        except Exception:
            return

        msg_type = data.get("type", "plaintext-message")
        if msg_type == "plaintext-message":
            await self._handle_plaintext(data)
        elif msg_type == "encrypted-message":
            await self._handle_encrypted(data)

    async def _handle_plaintext(self, data):
        """Незашифрованные сообщения (задание №1)."""
        receiver_name = data.get("receiver")
        text = data.get("content", "")
        if not receiver_name or not text:
            return

        try:
            receiver = await sync_to_async(User.objects.get)(username=receiver_name)
        except User.DoesNotExist:
            await self.send(json.dumps({"error": f"User '{receiver_name}' not found"}))
            return

        await sync_to_async(Message.objects.create)(
            sender=self.user, receiver=receiver, content=text
        )
        await self._log(f"Sent plaintext -> {receiver.username}")

        await self.channel_layer.group_send(
            f"user_{receiver.username}",
            {
                "type": "chat_message",
                "data": {
                    "type": "plaintext-message",
                    "sender": self.user.username,
                    "receiver": receiver.username,
                    "content": text,
                },
            },
        )

    async def _handle_encrypted(self, data):
        """DH + AES + подпись."""
        receiver_name = data.get("receiver")
        if not receiver_name:
            return
        try:
            receiver = await sync_to_async(User.objects.get)(username=receiver_name)
        except User.DoesNotExist:
            await self.send(json.dumps({"error": f"User '{receiver_name}' not found"}))
            return

        secret_b64 = data.get("shared_secret")
        nonce_b64 = data.get("nonce")
        ciphertext_b64 = data.get("ciphertext")
        tag_b64 = data.get("tag")
        signature_b64 = data.get("signature")

        # --- AES‑GCM расшифровка ---
        try:
            key = base64.b64decode(secret_b64)
            nonce = base64.b64decode(nonce_b64)
            ciphertext = base64.b64decode(ciphertext_b64)
            tag = base64.b64decode(tag_b64)
            aes = AESGCM(key)
            plaintext = aes.decrypt(nonce, ciphertext + tag, None).decode("utf-8", "ignore")
        except Exception as e:
            print(f"[AES] ❌ {e}")
            plaintext = "[decrypt_error]"
            await self._log(f"Decrypt failed ({receiver.username})")

        # --- Проверка подписи ---
        verified = False
        try:
            if hasattr(self.user, "public_key"):
                pk_bytes = base64.b64decode(self.user.public_key)
                pub = ed25519.Ed25519PublicKey.from_public_bytes(pk_bytes)
                pub.verify(base64.b64decode(signature_b64), plaintext.encode("utf-8"))
                verified = True
        except Exception:
            pass
        if not verified:
            plaintext = f"[SIGNATURE INVALID] {plaintext}"
            await self._log("Signature invalid")

        # --- Сохраняем и отправляем ---
        await sync_to_async(Message.objects.create)(
            sender=self.user, receiver=receiver, content=plaintext
        )
        await self._log(f"Sent encrypted -> {receiver.username}")

        await self.channel_layer.group_send(
            f"user_{receiver.username}",
            {
                "type": "chat_message",
                "data": {
                    "type": "plaintext-message",
                    "sender": self.user.username,
                    "receiver": receiver.username,
                    "content": plaintext,
                },
            },
        )

    async def chat_message(self, event):
        await self.send(json.dumps(event["data"]))

    async def _log(self, text):
        await sync_to_async(AuditLog.objects.create)(
            user=self.user, action=text, timestamp=timezone.now()
        )