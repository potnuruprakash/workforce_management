"""
Tenant isolation middleware.
Attaches the active tenant organization and current role to the request context.
"""

from apps.organizations.models import Organization
from apps.accounts.models import OrganizationMembership, Role


class TenantMiddleware:
    """
    Middleware that establishes tenant context for every request based on:
    1. Authenticated user's active organization membership.
    2. Session-based organization switching for multi-tenant users / super admins.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.active_organization = None
        request.active_membership = None
        request.active_role = None
        request.user_memberships = []

        if request.user.is_authenticated:
            # Super admins can view any organization or global platform
            if request.user.is_superuser:
                request.active_role = Role.SUPER_ADMIN
                session_org_id = request.session.get('active_organization_id')
                if session_org_id:
                    try:
                        request.active_organization = Organization.objects.filter(is_active=True).get(pk=session_org_id)
                    except Organization.DoesNotExist:
                        request.session.pop('active_organization_id', None)
                        request.active_organization = Organization.objects.filter(is_active=True).first()
                else:
                    request.active_organization = Organization.objects.filter(is_active=True).first()
            else:
                # Regular users: get their active memberships
                memberships = list(
                    OrganizationMembership.objects.filter(
                        user=request.user,
                        is_active=True,
                        organization__is_active=True
                    ).select_related('organization')
                )
                request.user_memberships = memberships

                if memberships:
                    session_org_id = request.session.get('active_organization_id')
                    selected_membership = None

                    if session_org_id:
                        selected_membership = next(
                            (m for m in memberships if m.organization_id == int(session_org_id)),
                            None
                        )

                    if not selected_membership:
                        # Fallback to default or first membership
                        selected_membership = next(
                            (m for m in memberships if m.is_default),
                            memberships[0]
                        )
                        request.session['active_organization_id'] = selected_membership.organization_id

                    request.active_organization = selected_membership.organization
                    request.active_membership = selected_membership
                    request.active_role = selected_membership.role

        response = self.get_response(request)
        return response
