from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import UserProfile, Message, AuditLog
from .serializers import AuditLogSerializer

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        public_key = request.data.get("public_key")

        if not all([username, password, public_key]):
            return Response({"error": "Missing fields"}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({"error": "User exists"}, status=400)

        user = User.objects.create_user(username=username, password=password)
        UserProfile.objects.create(user=user, public_key=public_key)
        return Response({"status": "ok"}, status=201)

class SaveKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        public_key = request.data.get("public_key")
        if not public_key:
            return Response({"error": "No key"}, status=400)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.public_key = public_key
        profile.save()
        AuditLog.objects.create(user=request.user, action="Updated public key")
        return Response({"status": "ok"})

class AuditLogListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logs = AuditLog.objects.filter(user=request.user).order_by("-timestamp")
        return Response(AuditLogSerializer(logs, many=True).data)