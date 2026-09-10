"""
Views for in-app notification center.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from apps.notifications.models import Notification


@login_required
def notification_list(request):
    """
    Displays all notifications for the current user.
    """
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    paginator = Paginator(notifications, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'notifications/list.html', {
        'page_obj': page_obj,
    })


@login_required
def mark_notification_read(request, pk):
    """
    Marks a single notification as read and redirects to link if available.
    """
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])

    if notification.link:
        return redirect(notification.link)
    return redirect('notifications:list')


@login_required
def mark_all_notifications_read(request):
    """
    Marks all notifications for this user as read.
    """
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('notifications:list')
