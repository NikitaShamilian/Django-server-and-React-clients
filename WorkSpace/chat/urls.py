from django.urls import path
from .views import MessageCreateView, AuditLogListView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("send/", MessageCreateView.as_view(), name="send_message"),
    path("audit/", AuditLogListView.as_view(), name="audit_log"),
]