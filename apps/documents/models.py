"""
Document management models for employee attachments and verification.
"""

from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel
from apps.employees.models import Employee


class DocumentType(models.TextChoices):
    RESUME = 'RESUME', 'Resume / CV'
    ID_PROOF = 'ID_PROOF', 'Government ID Proof'
    QUALIFICATION = 'QUALIFICATION', 'Degree / Certificate'
    EXPERIENCE = 'EXPERIENCE', 'Experience Certificate'
    JOINING_LETTER = 'JOINING_LETTER', 'Appointment / Joining Letter'
    OTHER = 'OTHER', 'Other Document'


class VerificationStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Verification'
    VERIFIED = 'VERIFIED', 'Verified'
    REJECTED = 'REJECTED', 'Rejected'


class EmployeeDocument(TimeStampedModel):
    """
    Secure document attachments associated with an Employee.
    Enforces role-based download permissions and tenant boundaries.
    """
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='documents',
        db_index=True
    )
    document_name = models.CharField(max_length=200, help_text="e.g. Master Degree Certificate, Passport Copy")
    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
        db_index=True
    )
    file = models.FileField(upload_to='documents/%Y/%m/')
    file_size = models.PositiveIntegerField(default=0, help_text="Size in bytes")
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_documents'
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True
    )
    expiry_date = models.DateField(null=True, blank=True, help_text="Optional expiry date for IDs or licenses")
    notes = models.TextField(blank=True, help_text="Verification remarks or notes")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Employee Document'
        verbose_name_plural = 'Employee Documents'

    def __str__(self):
        return f"{self.document_name} ({self.get_document_type_display()}) - {self.employee.full_name}"

    def save(self, *args, **kwargs):
        if self.file and hasattr(self.file, 'size') and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
