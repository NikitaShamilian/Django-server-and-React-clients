from django.urls import path
from .views import RegisterView, SaveKeyView, AuditLogListView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("save_key/", SaveKeyView.as_view()),
    path("audit_logs/", AuditLogListView.as_view()),
]