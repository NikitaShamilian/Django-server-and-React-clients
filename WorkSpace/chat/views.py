from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

from .models import UserProfile, Message, AuditLog
from .serializers import MessageSerializer, AuditLogSerializer


class RegisterView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        public_key = request.data.get("public_key")

        if not username or not password or not public_key:
            return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, password=password)
        UserProfile.objects.create(user=user, public_key=public_key)
        return Response({"success": True, "username": user.username}, status=status.HTTP_201_CREATED)


class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        sender = self.request.user
        receiver_id = self.request.data.get("receiver")
        content = self.request.data.get("content")
        signature = self.request.data.get("signature")

        from django.contrib.auth.models import User
        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            raise ValueError("Receiver not found")

        if not hasattr(sender, "profile") or not sender.profile.public_key:
            raise ValueError("Sender has no registered public key")

        public_key = load_pem_public_key(sender.profile.public_key.encode("utf-8"))

        try:
            public_key.verify(
                bytes.fromhex(signature),
                content.encode(),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        except Exception:
            raise ValueError("Signature verification failed")

        message = serializer.save(sender=sender, receiver=receiver, signature=signature)
        AuditLog.objects.create(user=sender, action=f"Sent message to {receiver.username}")
        return message


class AuditLogListView(generics.ListAPIView):
    queryset = AuditLog.objects.all().order_by("-timestamp")
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]