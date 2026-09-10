"""
Context processors providing tenant and role context to all templates.
"""

from apps.accounts.models import Role
from apps.organizations.models import Organization


def tenant_context(request):
    """
    Exposes tenant and role properties to Django templates.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {
            'active_organization': None,
            'active_role': None,
            'user_memberships': [],
            'is_super_admin': False,
            'is_org_admin': False,
            'is_manager': False,
            'all_organizations': [],
        }

    is_super = request.user.is_superuser or getattr(request, 'active_role', None) == Role.SUPER_ADMIN
    active_role = getattr(request, 'active_role', None)
    is_org_admin = is_super or active_role in (Role.OWNER, Role.HR_ADMIN)
    is_manager = is_super or active_role in (Role.OWNER, Role.HR_ADMIN, Role.MANAGER)

    return {
        'active_organization': getattr(request, 'active_organization', None),
        'active_role': active_role,
        'user_memberships': getattr(request, 'user_memberships', []),
        'is_super_admin': is_super,
        'is_org_admin': is_org_admin,
        'is_manager': is_manager,
        'all_organizations': Organization.objects.filter(is_active=True).order_by('name') if is_super else [],
    }
