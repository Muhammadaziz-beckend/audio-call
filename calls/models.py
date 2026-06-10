from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Call(models.Model):
    STATUS_CHOICES = [
        ("waiting", "Ожидание"),
        ("active", "Активный"),
        ("ended", "Завершён"),
        ("missed", "Пропущен"),
    ]

    caller_name = models.CharField(max_length=255, verbose_name="Имя звонящего")
    caller_phone = models.CharField(max_length=50, verbose_name="Телефон звонящего")
    manager = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="calls",
        verbose_name="Менеджер",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="waiting",
        verbose_name="Статус",
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Начало")
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name="Конец")
    duration = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Длительность (сек)"
    )
    room_id = models.CharField(
        max_length=100, unique=True, verbose_name="ID комнаты WebRTC"
    )

    class Meta:
        verbose_name = "Звонок"
        verbose_name_plural = "Звонки"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.caller_name} → {self.manager or 'не назначен'} [{self.status}]"


class ManagerStatus(models.Model):
    STATUS_CHOICES = [
        ("available", "Свободен"),
        ("busy", "Занят"),
        ("offline", "Офлайн"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="manager_status",
        verbose_name="Менеджер",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="offline",
        verbose_name="Статус",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Статус менеджера"
        verbose_name_plural = "Статусы менеджеров"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.status}"