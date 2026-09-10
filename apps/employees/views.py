"""
Views for Employee CRUD, profile viewing, search, filtering, and lifecycle management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.exceptions import PermissionDenied

from apps.employees.models import Employee, EmploymentStatus, Gender
from apps.employees.forms import EmployeeForm
from apps.departments.models import Department
from apps.accounts.models import Role
from apps.core.permissions import tenant_required, org_admin_required, manager_required
from apps.audit.services import log_action
from apps.audit.models import AuditAction
from apps.notifications.services import create_notification
from apps.notifications.models import NotificationType


@tenant_required
def employee_list(request):
    """
    Employee directory with multi-field search, multi-filtering, and pagination.
    Strictly isolated to request.active_organization.
    """
    org = request.active_organization
    query = request.GET.get('q', '').strip()
    dept_id = request.GET.get('department', '').strip()
    status = request.GET.get('status', '').strip()
    view_scope = request.GET.get('view_scope', 'active').strip()  # active, archived, all

    employees = Employee.objects.filter(organization=org).select_related('department', 'organization')

    # If the user is a Department Manager (and not Owner/Admin), scope to their department
    if getattr(request, 'active_role', None) == Role.MANAGER and not request.user.is_superuser:
        managed_dept_ids = Department.objects.filter(organization=org, manager__user=request.user).values_list('id', flat=True)
        if managed_dept_ids:
            employees = employees.filter(department_id__in=managed_dept_ids)

    # Lifecycle / Archive filter
    if view_scope == 'archived':
        employees = employees.filter(is_archived=True)
    elif view_scope == 'active':
        employees = employees.filter(is_archived=False)

    # Multi-field search
    if query:
        employees = employees.filter(
            Q(employee_id__icontains=query) |
            Q(full_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(designation__icontains=query) |
            Q(department__name__icontains=query)
        )

    # Filters
    if dept_id:
        employees = employees.filter(department_id=dept_id)
    if status:
        employees = employees.filter(employment_status=status)

    departments = Department.objects.filter(organization=org, is_active=True).order_by('name')

    # Pagination
    paginator = Paginator(employees.order_by('full_name'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate metrics for filter bar
    total_active = Employee.objects.filter(organization=org, is_archived=False).count()
    total_archived = Employee.objects.filter(organization=org, is_archived=True).count()

    return render(request, 'employees/list.html', {
        'page_obj': page_obj,
        'query': query,
        'selected_dept': dept_id,
        'selected_status': status,
        'view_scope': view_scope,
        'departments': departments,
        'status_choices': EmploymentStatus.choices,
        'organization': org,
        'total_active': total_active,
        'total_archived': total_archived,
    })


@tenant_required
def employee_detail(request, pk):
    """
    Comprehensive employee profile page with personal, employment, documents, and audit history.
    """
    org = request.active_organization
    employee = get_object_or_404(Employee.objects.select_related('organization', 'department', 'user'), pk=pk)

    # Enforce tenant boundary
    if employee.organization_id != org.id and not request.user.is_superuser:
        messages.error(request, "Access denied: Employee belongs to a different organization.")
        raise PermissionDenied("Tenant boundary violation.")

    # Check permission if user is regular employee
    if getattr(request, 'active_role', None) == Role.EMPLOYEE and not request.user.is_superuser:
        if employee.user != request.user:
            messages.error(request, "Access denied: You are only permitted to view your own profile.")
            raise PermissionDenied("Profile access restricted.")

    documents = employee.documents.select_related('uploaded_by').order_by('-created_at')
    recent_audits = employee.organization.audit_logs.filter(
        entity_type='Employee',
        entity_id=str(employee.pk)
    ).order_by('-timestamp')[:5]

    return render(request, 'employees/profile.html', {
        'employee': employee,
        'documents': documents,
        'recent_audits': recent_audits,
        'organization': org,
    })


@org_admin_required
@tenant_required
def employee_create(request):
    """
    Adds a new employee/staff record to the active organization.
    """
    org = request.active_organization

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, organization=org)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.organization = org
            employee.save()

            log_action(
                request,
                action=AuditAction.CREATE,
                entity_type='Employee',
                entity_id=employee.pk,
                description=f"Created employee record for {employee.full_name} ({employee.employee_id}) in {employee.department.name}."
            )

            messages.success(request, f"Employee '{employee.full_name}' ({employee.employee_id}) added successfully.")
            return redirect('employees:detail', pk=employee.pk)
    else:
        form = EmployeeForm(organization=org)

    return render(request, 'employees/form.html', {
        'form': form,
        'title': f"Add New Employee - {org.name}",
        'is_edit': False,
        'organization': org,
    })


@org_admin_required
@tenant_required
def employee_update(request, pk):
    """
    Updates an employee record, strictly enforcing tenant isolation.
    """
    org = request.active_organization
    employee = get_object_or_404(Employee, pk=pk)

    if employee.organization_id != org.id and not request.user.is_superuser:
        messages.error(request, "Access denied: Cannot edit employee from another organization.")
        raise PermissionDenied("Tenant boundary violation.")

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee, organization=org)
        if form.is_valid():
            employee = form.save()
            log_action(
                request,
                action=AuditAction.UPDATE,
                entity_type='Employee',
                entity_id=employee.pk,
                description=f"Updated details for employee {employee.full_name} ({employee.employee_id})."
            )
            messages.success(request, f"Employee '{employee.full_name}' updated successfully.")
            return redirect('employees:detail', pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee, organization=org)

    return render(request, 'employees/form.html', {
        'form': form,
        'employee': employee,
        'title': f"Edit Employee - {employee.full_name}",
        'is_edit': True,
        'organization': org,
    })


@org_admin_required
@tenant_required
def employee_archive(request, pk):
    """
    Archives an employee (soft delete) preserving historical records.
    """
    org = request.active_organization
    employee = get_object_or_404(Employee, pk=pk)

    if employee.organization_id != org.id and not request.user.is_superuser:
        messages.error(request, "Access denied: Tenant boundary violation.")
        raise PermissionDenied("Tenant boundary violation.")

    if request.method == 'POST':
        employee.employment_status = EmploymentStatus.ARCHIVED
        employee.archive(commit=True)

        log_action(
            request,
            action=AuditAction.ARCHIVE,
            entity_type='Employee',
            entity_id=employee.pk,
            description=f"Archived employee record {employee.full_name} ({employee.employee_id})."
        )
        messages.warning(request, f"Employee '{employee.full_name}' has been safely archived.")
        return redirect('employees:list')

    return render(request, 'employees/confirm_archive.html', {
        'employee': employee,
        'organization': org,
    })


@org_admin_required
@tenant_required
def employee_restore(request, pk):
    """
    Restores an archived employee back to ACTIVE status.
    """
    org = request.active_organization
    employee = get_object_or_404(Employee, pk=pk)

    if employee.organization_id != org.id and not request.user.is_superuser:
        messages.error(request, "Access denied: Tenant boundary violation.")
        raise PermissionDenied("Tenant boundary violation.")

    if request.method == 'POST':
        employee.employment_status = EmploymentStatus.ACTIVE
        employee.restore(commit=True)

        log_action(
            request,
            action=AuditAction.RESTORE,
            entity_type='Employee',
            entity_id=employee.pk,
            description=f"Restored employee record {employee.full_name} ({employee.employee_id}) to Active status."
        )
        messages.success(request, f"Employee '{employee.full_name}' has been restored to Active status.")
        return redirect('employees:detail', pk=employee.pk)

    return redirect('employees:detail', pk=employee.pk)


@org_admin_required
@tenant_required
def employee_delete(request, pk):
    """
    Permanent hard deletion. Restricted to Organization Owners and Platform Super Admins.
    Requires POST request with confirmation.
    """
    org = request.active_organization
    employee = get_object_or_404(Employee, pk=pk)

    if employee.organization_id != org.id and not request.user.is_superuser:
        messages.error(request, "Access denied: Tenant boundary violation.")
        raise PermissionDenied("Tenant boundary violation.")

    is_owner = request.user.organization_memberships.filter(
        organization=org,
        role=Role.OWNER,
        is_active=True
    ).exists()

    if not (request.user.is_superuser or is_owner):
        messages.error(request, "Access denied: Hard deletion is strictly restricted to Organization Owners.")
        raise PermissionDenied("Only owners can hard delete.")

    if request.method == 'POST':
        name = employee.full_name
        emp_id = employee.employee_id
        employee.delete()

        log_action(
            request,
            action=AuditAction.DELETE,
            entity_type='Employee',
            entity_id=pk,
            description=f"Permanently deleted employee {name} ({emp_id}) from database."
        )
        messages.success(request, f"Employee record '{name}' was permanently deleted.")
        return redirect('employees:list')

    return redirect('employees:detail', pk=employee.pk)
