"""
Notification service for triggering in-app notices and alerts.
"""

from apps.notifications.models import Notification, NotificationType


def create_notification(recipient, title, message, organization=None, notification_type=NotificationType.INFO, link=''):
    """
    Creates an in-app notification for a user.
    """
    return Notification.objects.create(
        recipient=recipient,
        organization=organization,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
        is_read=False
    )
