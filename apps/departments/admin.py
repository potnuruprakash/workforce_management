from django.contrib import admin
from apps.departments.models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'organization', 'manager', 'is_active', 'created_at')
    list_filter = ('organization', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'organization__name')
    ordering = ('organization', 'name')
