"""
Context processor for in-app user notifications.
"""

from apps.notifications.models import Notification


def notification_context(request):
    """
    Supplies the unread notification count and latest notifications to navigation.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'recent_notifications': [],
        }

    notifications_qs = Notification.objects.filter(recipient=request.user, is_read=False)
    
    # Optionally scope to active organization if present
    if hasattr(request, 'active_organization') and request.active_organization:
        notifications_qs = notifications_qs.filter(organization=request.active_organization)

    unread_count = notifications_qs.count()
    recent_notifications = list(notifications_qs[:5])

    return {
        'unread_notifications_count': unread_count,
        'recent_notifications': recent_notifications,
    }
