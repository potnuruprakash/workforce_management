"""
Accounts and Role-Based Access Control (RBAC) models.
"""

from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel
from apps.organizations.models import Organization


class Role(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN', 'Platform Super Admin'
    OWNER = 'OWNER', 'Organization Owner'
    HR_ADMIN = 'HR_ADMIN', 'HR / Admin'
    MANAGER = 'MANAGER', 'Department Manager'
    EMPLOYEE = 'EMPLOYEE', 'Employee / Staff'


class OrganizationMembership(TimeStampedModel):
    """
    Links a Django User to a Tenant Organization with a specific Role.
    Supports multi-organization membership (e.g. an owner who owns multiple branches).
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organization_memberships'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        db_index=True
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Primary organization for this user upon login"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this membership is currently enabled"
    )

    class Meta:
        unique_together = ('user', 'organization')
        ordering = ['-is_default', 'organization__name']
        verbose_name = 'Organization Membership'
        verbose_name_plural = 'Organization Memberships'

    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        # If this is marked as default, unset default on other memberships of the same user
        if self.is_default:
            OrganizationMembership.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
