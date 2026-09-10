from django.contrib import admin
from apps.organizations.models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization_type', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('organization_type', 'is_active', 'created_at')
    search_fields = ('name', 'email', 'phone', 'address')
    ordering = ('name',)
