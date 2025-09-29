from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Message, AuditLog, UserProfile


# Удаляем стандартную модель Group из сайдбара админки
admin.site.unregister(Group)


# --- Наши модели ---

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "receiver", "short_content", "timestamp")
    list_filter = ("sender", "receiver", "timestamp")
    search_fields = ("sender__username", "receiver__username", "content")

    def short_content(self, obj):
        return (obj.content[:40] + "...") if len(obj.content) > 40 else obj.content
    short_content.short_description = "Content"


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "action", "timestamp")
    list_filter = ("user", "timestamp")
    search_fields = ("user__username", "action")


# --- Кастомный UserAdmin ---

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fk_name = "user"
    max_num = 1


class CustomUserAdmin(BaseUserAdmin):
    # какие поля отображаются в форме пользователя
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
    )
    inlines = [UserProfileInline]

    # список пользователей
    list_display = ("username", "email", "first_name", "last_name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("username", "email")


# Переопределяем стандартный UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)