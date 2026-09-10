from django.contrib import admin
from apps.documents.models import EmployeeDocument


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'document_name',
        'employee',
        'document_type',
        'verification_status',
        'uploaded_by',
        'file_size',
        'created_at'
    )
    list_filter = ('document_type', 'verification_status', 'created_at')
    search_fields = ('document_name', 'employee__full_name', 'employee__employee_id')
    ordering = ('-created_at',)
