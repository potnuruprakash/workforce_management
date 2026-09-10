from django.contrib import admin
from apps.accounts.models import OrganizationMembership


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role', 'is_default', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'is_default', 'organization')
    search_fields = ('user__username', 'user__email', 'organization__name')
    ordering = ('organization', 'user')
