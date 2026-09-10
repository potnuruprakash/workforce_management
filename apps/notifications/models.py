"""
Notification models for in-app alerts and announcements.
"""

from django.db import models
from django.contrib.auth.models import User
from apps.organizations.models import Organization


class NotificationType(models.TextChoices):
    INFO = 'INFO', 'Information'
    SUCCESS = 'SUCCESS', 'Success'
    WARNING = 'WARNING', 'Warning'
    ALERT = 'ALERT', 'Alert'


class Notification(models.Model):
    """
    In-app notifications sent to specific users within an organization.
    """
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO
    )
    link = models.CharField(max_length=255, blank=True, help_text="Optional URL to navigate to")
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"{self.title} -> {self.recipient.username}"
