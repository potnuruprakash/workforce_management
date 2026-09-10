"""
Audit logging service for tracking critical workforce actions.
"""

from apps.audit.models import AuditLog


def get_client_ip(request):
    """Safely retrieves client IP address from request."""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_action(request, action, entity_type, entity_id, description, organization=None):
    """
    Records an immutable audit trail entry.
    """
    user = request.user if request and request.user.is_authenticated else None
    org = organization
    if not org and request and hasattr(request, 'active_organization'):
        org = request.active_organization

    ip = get_client_ip(request) if request else None

    return AuditLog.objects.create(
        user=user,
        organization=org,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else '',
        description=description,
        ip_address=ip
    )
