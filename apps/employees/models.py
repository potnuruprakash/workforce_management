"""
Employee domain models for Workforce Management Platform.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel, SoftDeleteModel
from apps.organizations.models import Organization
from apps.departments.models import Department


class EmploymentStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    ON_LEAVE = 'ON_LEAVE', 'On Leave'
    RESIGNED = 'RESIGNED', 'Resigned'
    RETIRED = 'RETIRED', 'Retired'
    TERMINATED = 'TERMINATED', 'Terminated'
    ARCHIVED = 'ARCHIVED', 'Archived'


class Gender(models.TextChoices):
    MALE = 'MALE', 'Male'
    FEMALE = 'FEMALE', 'Female'
    OTHER = 'OTHER', 'Other'
    PREFER_NOT_TO_SAY = 'PREFER_NOT_TO_SAY', 'Prefer not to say'


class Employee(TimeStampedModel, SoftDeleteModel):
    """
    Core Employee and Staff model.
    Scoped to an Organization and Department with strict referential integrity.
    """
    employee_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Organization-specific Employee/Staff ID (e.g. EMP-101, FAC-204, DR-501)"
    )
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee_profile',
        help_text="Optional login user account for employee self-service portal"
    )
    full_name = models.CharField(max_length=200, db_index=True)
    date_of_birth = models.DateField(help_text="Date of birth")
    gender = models.CharField(max_length=20, choices=Gender.choices, default=Gender.PREFER_NOT_TO_SAY)
    email = models.EmailField(db_index=True, help_text="Work or personal email address")
    phone_number = models.CharField(max_length=30, help_text="Contact telephone/mobile number")
    address = models.TextField(help_text="Permanent or residential address")

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='employees',
        db_index=True,
        help_text="Tenant organization"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='employees',
        db_index=True,
        help_text="Department within the organization"
    )
    designation = models.CharField(
        max_length=150,
        db_index=True,
        help_text="e.g. Senior Software Engineer, Assistant Professor, Staff Nurse"
    )
    qualification = models.CharField(
        max_length=200,
        help_text="Highest qualification (e.g. M.Tech in CSE, Ph.D, MBBS, MD, MBA)"
    )
    bio = models.TextField(blank=True, help_text="Professional summary or biography")
    joining_date = models.DateField(db_index=True, help_text="Date the employee joined the organization")
    employment_status = models.CharField(
        max_length=20,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.ACTIVE,
        db_index=True
    )
    profile_photo = models.ImageField(
        upload_to='employee_photos/',
        blank=True,
        null=True,
        help_text="Passport-style photo or avatar"
    )

    class Meta:
        unique_together = ('organization', 'employee_id')
        ordering = ['organization', 'full_name']
        indexes = [
            models.Index(fields=['organization', 'employment_status']),
            models.Index(fields=['organization', 'department']),
        ]
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'

    def __str__(self):
        return f"{self.full_name} ({self.employee_id}) - {self.organization.name}"

    def clean(self):
        super().clean()
        # Enforce that department belongs to the employee's organization
        if self.department_id and self.organization_id:
            if self.department.organization_id != self.organization_id:
                raise ValidationError({
                    'department': f"The selected department '{self.department.name}' does not belong to {self.organization.name}."
                })

    def save(self, *args, **kwargs):
        self.clean()
        # If marked as ARCHIVED status, automatically set is_archived flag
        if self.employment_status == EmploymentStatus.ARCHIVED:
            self.is_archived = True
        super().save(*args, **kwargs)

    @property
    def is_active_employee(self):
        return self.employment_status == EmploymentStatus.ACTIVE and not self.is_archived
