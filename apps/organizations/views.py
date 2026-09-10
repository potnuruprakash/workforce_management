"""
Views for Organization tenant management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.core.exceptions import PermissionDenied

from apps.organizations.models import Organization
from apps.organizations.forms import OrganizationForm
from apps.accounts.models import Role, OrganizationMembership
from apps.core.permissions import super_admin_required, org_admin_required
from apps.audit.services import log_action
from apps.audit.models import AuditAction


@login_required
def organization_list(request):
    """
    Lists all tenant organizations.
    Restricted to Platform Super Admins.
    """
    if not request.user.is_superuser and getattr(request, 'active_role', None) != Role.SUPER_ADMIN:
        messages.error(request, "Access restricted to Platform Super Administrators.")
        raise PermissionDenied("Platform Super Admin privilege required.")

    query = request.GET.get('q', '').strip()
    org_type = request.GET.get('type', '').strip()
    status = request.GET.get('status', '').strip()

    orgs = Organization.objects.annotate(
        emp_count=Count('employees', filter=Q(employees__is_archived=False)),
        dept_count=Count('departments', filter=Q(departments__is_active=True))
    )

    if query:
        orgs = orgs.filter(Q(name__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query))
    if org_type:
        orgs = orgs.filter(organization_type=org_type)
    if status == 'active':
        orgs = orgs.filter(is_active=True)
    elif status == 'inactive':
        orgs = orgs.filter(is_active=False)

    paginator = Paginator(orgs.order_by('name'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'organizations/list.html', {
        'page_obj': page_obj,
        'query': query,
        'org_type': org_type,
        'status': status,
        'org_types': Organization.ORGANIZATION_TYPE_CHOICES,
    })


@login_required
def organization_detail(request, pk):
    """
    Details page for an organization.
    Super Admins can view any; regular users can only view their own organization.
    """
    org = get_object_or_404(Organization, pk=pk)

    if not request.user.is_superuser:
        user_org_ids = request.user.organization_memberships.filter(is_active=True).values_list('organization_id', flat=True)
        if org.id not in user_org_ids:
            messages.error(request, "Access denied: You cannot view other organizations' details.")
            raise PermissionDenied("Tenant isolation boundary enforced.")

    departments = org.departments.filter(is_active=True).order_by('name')
    memberships = org.memberships.filter(is_active=True).select_related('user').order_by('role', 'user__username')
    recent_employees = org.employees.filter(is_archived=False).order_by('-created_at')[:6]

    return render(request, 'organizations/detail.html', {
        'organization': org,
        'departments': departments,
        'memberships': memberships,
        'recent_employees': recent_employees,
    })


@super_admin_required
def organization_create(request):
    """
    Creates a new tenant organization.
    """
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES)
        if form.is_valid():
            org = form.save()
            log_action(
                request,
                action=AuditAction.CREATE,
                entity_type='Organization',
                entity_id=org.pk,
                description=f"Created organization '{org.name}' ({org.get_organization_type_display()}).",
                organization=org
            )
            messages.success(request, f"Organization '{org.name}' created successfully.")
            return redirect('organizations:detail', pk=org.pk)
    else:
        form = OrganizationForm()

    return render(request, 'organizations/form.html', {
        'form': form,
        'title': 'Create New Organization',
        'is_edit': False,
    })


@login_required
def organization_update(request, pk):
    """
    Updates an existing organization.
    Allowed for Super Admin or Organization Owner.
    """
    org = get_object_or_404(Organization, pk=pk)

    # Permission check
    is_owner = request.user.organization_memberships.filter(
        organization=org,
        role=Role.OWNER,
        is_active=True
    ).exists()

    if not (request.user.is_superuser or is_owner):
        messages.error(request, "Access denied: Only Organization Owners or Super Admins can edit organization settings.")
        raise PermissionDenied("Insufficient privileges.")

    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES, instance=org)
        if form.is_valid():
            org = form.save()
            log_action(
                request,
                action=AuditAction.UPDATE,
                entity_type='Organization',
                entity_id=org.pk,
                description=f"Updated organization details for '{org.name}'.",
                organization=org
            )
            messages.success(request, f"Organization '{org.name}' updated successfully.")
            return redirect('organizations:detail', pk=org.pk)
    else:
        form = OrganizationForm(instance=org)

    return render(request, 'organizations/form.html', {
        'form': form,
        'organization': org,
        'title': f"Edit {org.name}",
        'is_edit': True,
    })
