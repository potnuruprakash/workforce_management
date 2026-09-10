"""
Core base models and managers for Workforce Management Platform.
"""

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides self-updating
    created_at and updated_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ActiveManager(models.Manager):
    """
    QuerySet manager that defaults to non-archived records.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_archived=False)


class SoftDeleteModel(models.Model):
    """
    Abstract model supporting soft-delete/archiving.
    Preserves historical employee records as required by SaaS standards.
    """
    is_archived = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()  # Default manager (returns all including archived)
    active_objects = ActiveManager()  # Convenience manager for active records only

    class Meta:
        abstract = True

    def archive(self, commit=True):
        """Soft-delete/archive this record."""
        self.is_archived = True
        self.archived_at = timezone.now()
        if commit:
            self.save(update_fields=['is_archived', 'archived_at', 'updated_at'])

    def restore(self, commit=True):
        """Restore an archived record back to active state."""
        self.is_archived = False
        self.archived_at = None
        if commit:
            self.save(update_fields=['is_archived', 'archived_at', 'updated_at'])
