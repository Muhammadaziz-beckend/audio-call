from django.contrib import admin
from .models import Call, ManagerStatus
# Register your models here.



@admin.register(Call)
class CallAdmin(admin.ModelAdmin):

    list_display = ("caller_name", "caller_phone", "manager", "status", "started_at")
    list_filter = ("status", "started_at")
    search_fields = ("caller_name", "caller_phone", "manager__username")


@admin.register(ManagerStatus)
class ManagerStatusAdmin(admin.ModelAdmin):
    list_display = ("user", "status")
    list_filter = ("status",)
    search_fields = ("user__username",)