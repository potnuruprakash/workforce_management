"""
Audit logging models for compliance, security, and activity tracking.
"""

from django.db import models
from django.contrib.auth.models import User
from apps.organizations.models import Organization


class AuditAction(models.TextChoices):
    CREATE = 'CREATE', 'Created'
    UPDATE = 'UPDATE', 'Updated'
    ARCHIVE = 'ARCHIVE', 'Archived'
    RESTORE = 'RESTORE', 'Restored'
    DELETE = 'DELETE', 'Deleted'
    LOGIN = 'LOGIN', 'User Logged In'
    LOGOUT = 'LOGOUT', 'User Logged Out'
    DOCUMENT_UPLOAD = 'DOCUMENT_UPLOAD', 'Document Uploaded'
    DOCUMENT_VERIFY = 'DOCUMENT_VERIFY', 'Document Verified'
    ROLE_ASSIGN = 'ROLE_ASSIGN', 'Role Assigned'


class AuditLog(models.Model):
    """
    Immutable audit log entry recording actions performed by users.
    Scoped by organization for multi-tenant isolation.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='audit_logs',
        db_index=True
    )
    action = models.CharField(
        max_length=50,
        choices=AuditAction.choices,
        db_index=True
    )
    entity_type = models.CharField(max_length=100, db_index=True, help_text="e.g. Employee, Department, Organization")
    entity_id = models.CharField(max_length=100, blank=True, help_text="Primary key or identifier of the entity")
    description = models.TextField(help_text="Detailed audit message")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        actor = self.user.username if self.user else "System"
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {actor} - {self.action}: {self.description[:60]}"
