from django.contrib import admin
from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'organization', 'action', 'entity_type', 'entity_id', 'description')
    list_filter = ('action', 'entity_type', 'organization', 'timestamp')
    search_fields = ('description', 'user__username', 'organization__name', 'entity_id')
    readonly_fields = ('timestamp', 'user', 'organization', 'action', 'entity_type', 'entity_id', 'description', 'ip_address')
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
