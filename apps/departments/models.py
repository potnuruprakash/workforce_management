"""
Department models for multi-tenant organizations.
"""

from django.db import models
from apps.core.models import TimeStampedModel
from apps.organizations.models import Organization


class Department(TimeStampedModel):
    """
    Department/Division within an Organization.
    E.g. CSE / Mechanical (College), Engineering / Sales (Company), Cardiology (Hospital).
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='departments',
        help_text="Tenant organization that owns this department"
    )
    name = models.CharField(max_length=150, help_text="e.g. Computer Science, Human Resources, Cardiology")
    code = models.CharField(max_length=50, help_text="Short code unique within the organization, e.g. CSE, HR, CARD")
    description = models.TextField(blank=True, help_text="Mission or scope of the department")
    manager = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        help_text="Head of department or manager"
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        unique_together = ('organization', 'code')
        ordering = ['organization', 'name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def total_employees(self):
        return self.employees.filter(is_archived=False).count()

    @property
    def active_employees(self):
        return self.employees.filter(is_archived=False, employment_status='ACTIVE').count()
