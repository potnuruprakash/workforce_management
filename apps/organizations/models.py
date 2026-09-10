"""
Organization domain models for multi-tenant Workforce Management.
"""

from django.db import models
from apps.core.models import TimeStampedModel


class Organization(TimeStampedModel):
    """
    Tenant Organization model.
    Represents colleges, universities, companies, hospitals, schools, NGOs, etc.
    """
    TYPE_COLLEGE = 'COLLEGE'
    TYPE_UNIVERSITY = 'UNIVERSITY'
    TYPE_SCHOOL = 'SCHOOL'
    TYPE_COMPANY = 'COMPANY'
    TYPE_HOSPITAL = 'HOSPITAL'
    TYPE_GOVERNMENT = 'GOVERNMENT'
    TYPE_PRIVATE = 'PRIVATE'
    TYPE_NGO = 'NGO'
    TYPE_OTHER = 'OTHER'

    ORGANIZATION_TYPE_CHOICES = [
        (TYPE_COLLEGE, 'College'),
        (TYPE_UNIVERSITY, 'University'),
        (TYPE_SCHOOL, 'School'),
        (TYPE_COMPANY, 'Company'),
        (TYPE_HOSPITAL, 'Hospital'),
        (TYPE_GOVERNMENT, 'Government Organization'),
        (TYPE_PRIVATE, 'Private Organization'),
        (TYPE_NGO, 'Non-Governmental Organization (NGO)'),
        (TYPE_OTHER, 'Other'),
    ]

    name = models.CharField(max_length=255, unique=True, help_text="Unique name of the organization")
    organization_type = models.CharField(
        max_length=30,
        choices=ORGANIZATION_TYPE_CHOICES,
        default=TYPE_COMPANY,
        db_index=True,
        help_text="Classification of the organization"
    )
    email = models.EmailField(help_text="Official contact email")
    phone = models.CharField(max_length=30, help_text="Primary phone number")
    address = models.TextField(help_text="Physical or postal address")
    website = models.URLField(max_length=255, blank=True, null=True, help_text="Official website")
    description = models.TextField(blank=True, help_text="Brief background or overview")
    logo = models.ImageField(upload_to='org_logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def __str__(self):
        return f"{self.name} ({self.get_organization_type_display()})"

    @property
    def total_employees(self):
        return self.employees.filter(is_archived=False).count()

    @property
    def active_employees(self):
        return self.employees.filter(is_archived=False, employment_status='ACTIVE').count()

    @property
    def total_departments(self):
        return self.departments.filter(is_active=True).count()
