"""
Automated tests for employee document management and access control.
"""

from datetime import date
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError

from apps.organizations.models import Organization
from apps.departments.models import Department
from apps.employees.models import Employee, EmploymentStatus, Gender
from apps.accounts.models import OrganizationMembership, Role
from apps.documents.models import EmployeeDocument, DocumentType
from apps.core.utils import validate_file_upload


class DocumentSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.org = Organization.objects.create(
            name="Security Org",
            organization_type=Organization.TYPE_COMPANY,
            email="sec@org.com",
            phone="123",
            address="Addr"
        )
        self.dept = Department.objects.create(
            organization=self.org,
            name="Security Dept",
            code="SEC"
        )

        # Employee 1
        self.user1 = User.objects.create_user(username="emp_user1", password="password123")
        OrganizationMembership.objects.create(user=self.user1, organization=self.org, role=Role.EMPLOYEE, is_default=True)
        self.emp1 = Employee.objects.create(
            organization=self.org,
            department=self.dept,
            user=self.user1,
            employee_id="E-01",
            full_name="User One",
            date_of_birth=date(1990, 1, 1),
            gender=Gender.MALE,
            email="u1@org.com",
            phone_number="111",
            address="Addr",
            designation="Analyst",
            qualification="B.Sc",
            joining_date=date(2022, 1, 1),
            employment_status=EmploymentStatus.ACTIVE
        )

        # Employee 2
        self.user2 = User.objects.create_user(username="emp_user2", password="password123")
        OrganizationMembership.objects.create(user=self.user2, organization=self.org, role=Role.EMPLOYEE, is_default=True)
        self.emp2 = Employee.objects.create(
            organization=self.org,
            department=self.dept,
            user=self.user2,
            employee_id="E-02",
            full_name="User Two",
            date_of_birth=date(1992, 2, 2),
            gender=Gender.FEMALE,
            email="u2@org.com",
            phone_number="222",
            address="Addr",
            designation="Analyst",
            qualification="B.Sc",
            joining_date=date(2022, 2, 1),
            employment_status=EmploymentStatus.ACTIVE
        )

        # Document belonging to Employee 1
        self.doc1 = EmployeeDocument.objects.create(
            employee=self.emp1,
            document_name="User1 Passport",
            document_type=DocumentType.ID_PROOF,
            file=SimpleUploadedFile("passport.pdf", b"Secret ID", content_type="application/pdf"),
            uploaded_by=self.user1
        )

    def test_file_extension_validator_rejects_unauthorized_types(self):
        """Uploading executable or unsafe files (e.g. .exe, .sh) must raise a ValidationError."""
        bad_file = SimpleUploadedFile("script.exe", b"malicious binary", content_type="application/octet-stream")
        with self.assertRaises(ValidationError):
            validate_file_upload(bad_file)

    def test_file_extension_validator_accepts_valid_documents(self):
        """PDF, DOC, DOCX, and images under 5MB pass validation."""
        valid_file = SimpleUploadedFile("resume.pdf", b"Valid resume content", content_type="application/pdf")
        try:
            validate_file_upload(valid_file)
        except ValidationError:
            self.fail("validate_file_upload raised ValidationError unexpectedly for a valid PDF!")

    def test_unauthorized_employee_cannot_download_other_employee_document(self):
        """Employee 2 should NOT be allowed to download Employee 1's private document (403 Forbidden)."""
        self.client.login(username="emp_user2", password="password123")
        response = self.client.get(reverse('documents:download', kwargs={'pk': self.doc1.pk}))
        self.assertEqual(response.status_code, 403)
