"""
Views for Department management with strict multi-tenant scoping.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.core.exceptions import PermissionDenied

from apps.departments.models import Department
from apps.departments.forms import DepartmentForm
from apps.core.permissions import tenant_required, org_admin_required
from apps.audit.services import log_action
from apps.audit.models import AuditAction


@tenant_required
def department_list(request):
    """
    Lists departments for the current active organization.
    """
    org = request.active_organization
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    departments = Department.objects.filter(organization=org).annotate(
        emp_count=Count('employees', filter=Q(employees__is_archived=False))
    ).select_related('manager')

    if query:
        departments = departments.filter(Q(name__icontains=query) | Q(code__icontains=query))
    if status == 'active':
        departments = departments.filter(is_active=True)
    elif status == 'inactive':
        departments = departments.filter(is_active=False)

    paginator = Paginator(departments.order_by('name'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'departments/list.html', {
        'page_obj': page_obj,
        'query': query,
        'status': status,
        'organization': org,
    })


@org_admin_required
@tenant_required
def department_create(request):
    """
    Creates a new department within the active organization.
    """
    org = request.active_organization

    if request.method == 'POST':
        form = DepartmentForm(request.POST, organization=org)
        if form.is_valid():
            department = form.save(commit=False)
            department.organization = org
            department.save()

            log_action(
                request,
                action=AuditAction.CREATE,
                entity_type='Department',
                entity_id=department.pk,
                description=f"Created department '{department.name}' ({department.code}) in {org.name}."
            )
            messages.success(request, f"Department '{department.name}' created successfully.")
            return redirect('departments:list')
    else:
        form = DepartmentForm(organization=org)

    return render(request, 'departments/form.html', {
        'form': form,
        'title': f"Add Department - {org.name}",
        'is_edit': False,
        'organization': org,
    })


@org_admin_required
@tenant_required
def department_update(request, pk):
    """
    Updates a department, ensuring tenant isolation.
    """
    org = request.active_organization
    department = get_object_or_404(Department, pk=pk)

    # Strictly verify tenant isolation
    if department.organization_id != org.id and not request.user.is_superuser:
        messages.error(request, "Access denied: This department belongs to another organization.")
        raise PermissionDenied("Tenant boundary violation.")

    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department, organization=org)
        if form.is_valid():
            department = form.save()
            log_action(
                request,
                action=AuditAction.UPDATE,
                entity_type='Department',
                entity_id=department.pk,
                description=f"Updated department '{department.name}' ({department.code})."
            )
            messages.success(request, f"Department '{department.name}' updated successfully.")
            return redirect('departments:list')
    else:
        form = DepartmentForm(instance=department, organization=org)

    return render(request, 'departments/form.html', {
        'form': form,
        'department': department,
        'title': f"Edit Department - {department.name}",
        'is_edit': True,
        'organization': org,
    })


@org_admin_required
@tenant_required
def department_delete(request, pk):
    """
    Safely deletes a department if no employees are assigned to it.
    """
    org = request.active_organization
    department = get_object_or_404(Department, pk=pk)

    # Tenant boundary enforcement
    if department.organization_id != org.id and not request.user.is_superuser:
        messages.error(request, "Access denied: Cannot delete department from another organization.")
        raise PermissionDenied("Tenant boundary violation.")

    # Referential integrity guard: check if any employees exist
    employee_count = department.employees.count()
    if employee_count > 0:
        messages.error(
            request,
            f"Cannot delete department '{department.name}': There are currently {employee_count} employee(s) assigned to this department. Reassign or archive them first."
        )
        return redirect('departments:list')

    dept_name = department.name
    dept_code = department.code
    department.delete()

    log_action(
        request,
        action=AuditAction.DELETE,
        entity_type='Department',
        entity_id=pk,
        description=f"Deleted department '{dept_name}' ({dept_code}) from {org.name}."
    )
    messages.success(request, f"Department '{dept_name}' was successfully deleted.")
    return redirect('departments:list')
