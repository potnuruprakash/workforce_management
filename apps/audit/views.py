"""
Views for viewing and filtering immutable audit logs.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

from apps.audit.models import AuditLog, AuditAction
from apps.core.permissions import org_admin_required, tenant_required


@org_admin_required
@tenant_required
def audit_list(request):
    """
    Displays audit history scoped to the active organization.
    Platform Super Admins can see all logs across organizations.
    """
    org = request.active_organization
    query = request.GET.get('q', '').strip()
    action_filter = request.GET.get('action', '').strip()
    entity_filter = request.GET.get('entity', '').strip()

    if request.user.is_superuser:
        logs = AuditLog.objects.all()
    else:
        logs = AuditLog.objects.filter(organization=org)

    logs = logs.select_related('user', 'organization')

    if query:
        logs = logs.filter(
            Q(description__icontains=query) |
            Q(entity_id__icontains=query) |
            Q(user__username__icontains=query)
        )
    if action_filter:
        logs = logs.filter(action=action_filter)
    if entity_filter:
        logs = logs.filter(entity_type=entity_filter)

    paginator = Paginator(logs.order_by('-timestamp'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'audit/list.html', {
        'page_obj': page_obj,
        'query': query,
        'action_filter': action_filter,
        'entity_filter': entity_filter,
        'actions': AuditAction.choices,
        'organization': org,
    })
