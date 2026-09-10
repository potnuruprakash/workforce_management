"""
Views for Organization Tenant Dashboard and Platform Super Admin Dashboard.
"""

import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from apps.organizations.models import Organization
from apps.departments.models import Department
from apps.employees.models import Employee, EmploymentStatus
from apps.accounts.models import Role, OrganizationMembership
from apps.audit.models import AuditLog
from apps.core.permissions import super_admin_required


@login_required
def dashboard_index(request):
    """
    Main dashboard router. Routes Super Admins to Platform Dashboard
    or Tenant Organization Dashboard based on user context.
    """
    is_super = request.user.is_superuser or getattr(request, 'active_role', None) == Role.SUPER_ADMIN
    view_param = request.GET.get('view')

    # If explicitly requested platform view or no active org exists for superuser
    if is_super and (view_param == 'platform' or not request.active_organization):
        return platform_dashboard(request)

    org = request.active_organization
    if not org:
        if is_super:
            return redirect('dashboard:platform')
        return redirect('accounts:profile')

    # Calculate Organization Metrics
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    employees_qs = Employee.objects.filter(organization=org)
    total_employees = employees_qs.filter(is_archived=False).count()
    active_employees = employees_qs.filter(is_archived=False, employment_status=EmploymentStatus.ACTIVE).count()
    on_leave_employees = employees_qs.filter(is_archived=False, employment_status=EmploymentStatus.ON_LEAVE).count()
    exited_employees = employees_qs.filter(
        employment_status__in=[EmploymentStatus.RESIGNED, EmploymentStatus.RETIRED, EmploymentStatus.TERMINATED]
    ).count()
    new_this_month = employees_qs.filter(is_archived=False, joining_date__gte=thirty_days_ago.date()).count()

    total_departments = Department.objects.filter(organization=org, is_active=True).count()

    # Department distribution for Chart.js
    dept_stats = Department.objects.filter(organization=org, is_active=True).annotate(
        count=Count('employees', filter=Q(employees__is_archived=False))
    ).order_by('-count')[:8]

    dept_labels = [d.name for d in dept_stats]
    dept_counts = [d.count for d in dept_stats]

    # Status distribution
    status_counts_dict = dict(
        employees_qs.values('employment_status').annotate(count=Count('id')).values_list('employment_status', 'count')
    )
    status_labels = ['Active', 'On Leave', 'Resigned', 'Retired', 'Terminated']
    status_data = [
        status_counts_dict.get(EmploymentStatus.ACTIVE, 0),
        status_counts_dict.get(EmploymentStatus.ON_LEAVE, 0),
        status_counts_dict.get(EmploymentStatus.RESIGNED, 0),
        status_counts_dict.get(EmploymentStatus.RETIRED, 0),
        status_counts_dict.get(EmploymentStatus.TERMINATED, 0),
    ]

    # Recent Records
    recent_employees = employees_qs.filter(is_archived=False).select_related('department').order_by('-created_at')[:5]
    recent_audits = org.audit_logs.select_related('user').order_by('-timestamp')[:6]

    return render(request, 'dashboard/organization.html', {
        'organization': org,
        'total_employees': total_employees,
        'active_employees': active_employees,
        'on_leave_employees': on_leave_employees,
        'exited_employees': exited_employees,
        'new_this_month': new_this_month,
        'total_departments': total_departments,
        'dept_labels_json': json.dumps(dept_labels),
        'dept_counts_json': json.dumps(dept_counts),
        'status_labels_json': json.dumps(status_labels),
        'status_data_json': json.dumps(status_data),
        'recent_employees': recent_employees,
        'recent_audits': recent_audits,
        'is_super_admin': is_super,
    })


@super_admin_required
def platform_dashboard(request):
    """
    Platform Super Admin dashboard for overall SaaS platform telemetry.
    """
    total_organizations = Organization.objects.count()
    active_organizations = Organization.objects.filter(is_active=True).count()
    total_employees = Employee.objects.filter(is_archived=False).count()
    total_users = OrganizationMembership.objects.values('user').distinct().count()

    # Organization types breakdown
    org_type_counts = Organization.objects.values('organization_type').annotate(
        count=Count('id')
    ).order_by('-count')

    type_labels = [dict(Organization.ORGANIZATION_TYPE_CHOICES).get(item['organization_type'], item['organization_type']) for item in org_type_counts]
    type_data = [item['count'] for item in org_type_counts]

    recent_orgs = Organization.objects.annotate(
        emp_count=Count('employees', filter=Q(employees__is_archived=False)),
        dept_count=Count('departments', filter=Q(departments__is_active=True))
    ).order_by('-created_at')[:6]

    recent_platform_audits = AuditLog.objects.select_related('user', 'organization').order_by('-timestamp')[:8]

    return render(request, 'dashboard/platform.html', {
        'total_organizations': total_organizations,
        'active_organizations': active_organizations,
        'total_employees': total_employees,
        'total_users': total_users,
        'type_labels_json': json.dumps(type_labels),
        'type_data_json': json.dumps(type_data),
        'recent_orgs': recent_orgs,
        'recent_platform_audits': recent_platform_audits,
    })
