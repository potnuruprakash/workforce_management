from django.contrib import admin
from apps.employees.models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'employee_id',
        'full_name',
        'organization',
        'department',
        'designation',
        'employment_status',
        'joining_date',
        'is_archived'
    )
    list_filter = (
        'organization',
        'employment_status',
        'is_archived',
        'gender',
        'joining_date'
    )
    search_fields = (
        'employee_id',
        'full_name',
        'email',
        'phone_number',
        'designation',
        'organization__name',
        'department__name'
    )
    ordering = ('organization', 'full_name')
