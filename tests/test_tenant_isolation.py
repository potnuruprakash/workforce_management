"""
Automated tests verifying multi-tenant isolation.
CRITICAL REQUIREMENT: Users from Organization A must NEVER be able
to access, view, or modify Organization B's data.
"""

from datetime import date
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.organizations.models import Organization
from apps.departments.models import Department
from apps.employees.models import Employee, EmploymentStatus, Gender
from apps.accounts.models import OrganizationMembership, Role
from apps.documents.models import EmployeeDocument, DocumentType


class TenantIsolationTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Tenant Org A (ABC Tech)
        self.org_a = Organization.objects.create(
            name="Org A Corp",
            organization_type=Organization.TYPE_COMPANY,
            email="contact@orga.com",
            phone="111-222-3333",
            address="123 Alpha St"
        )
        self.dept_a = Department.objects.create(
            organization=self.org_a,
            name="Engineering A",
            code="ENGA"
        )
        self.emp_a = Employee.objects.create(
            organization=self.org_a,
            department=self.dept_a,
            employee_id="A-101",
            full_name="Alice Alpha",
            date_of_birth=date(1990, 1, 1),
            gender=Gender.FEMALE,
            email="alice@orga.com",
            phone_number="111-0001",
            address="Alpha Residence",
            designation="Engineer",
            qualification="B.Tech",
            joining_date=date(2022, 1, 1),
            employment_status=EmploymentStatus.ACTIVE
        )

        # Create Tenant Org B (MVGR College)
        self.org_b = Organization.objects.create(
            name="Org B College",
            organization_type=Organization.TYPE_COLLEGE,
            email="contact@orgb.edu",
            phone="444-555-6666",
            address="456 Beta Ave"
        )
        self.dept_b = Department.objects.create(
            organization=self.org_b,
            name="CSE B",
            code="CSEB"
        )
        self.emp_b = Employee.objects.create(
            organization=self.org_b,
            department=self.dept_b,
            employee_id="B-201",
            full_name="Bob Beta",
            date_of_birth=date(1985, 5, 5),
            gender=Gender.MALE,
            email="bob@orgb.edu",
            phone_number="444-0002",
            address="Beta Quarters",
            designation="Professor",
            qualification="Ph.D",
            joining_date=date(2020, 1, 1),
            employment_status=EmploymentStatus.ACTIVE
        )

        # Create HR User for Org A
        self.user_a = User.objects.create_user(
            username="hr_user_a",
            email="hra@orga.com",
            password="password123"
        )
        OrganizationMembership.objects.create(
            user=self.user_a,
            organization=self.org_a,
            role=Role.HR_ADMIN,
            is_default=True
        )

        # Create HR User for Org B
        self.user_b = User.objects.create_user(
            username="hr_user_b",
            email="hrb@orgb.edu",
            password="password123"
        )
        OrganizationMembership.objects.create(
            user=self.user_b,
            organization=self.org_b,
            role=Role.HR_ADMIN,
            is_default=True
        )

    def test_org_a_user_sees_only_org_a_employees_in_list(self):
        """HR User of Org A should only see Alice, never Bob."""
        self.client.login(username="hr_user_a", password="password123")
        response = self.client.get(reverse('employees:list'))
        self.assertEqual(response.status_code, 200)

        employees_in_page = list(response.context['page_obj'])
        self.assertIn(self.emp_a, employees_in_page)
        self.assertNotIn(self.emp_b, employees_in_page)

    def test_org_a_user_cannot_access_org_b_employee_detail(self):
        """HR User of Org A attempting to view Org B's employee profile must receive 403 Forbidden."""
        self.client.login(username="hr_user_a", password="password123")
        response = self.client.get(reverse('employees:detail', kwargs={'pk': self.emp_b.pk}))
        self.assertEqual(response.status_code, 403)

    def test_org_a_user_cannot_edit_org_b_employee(self):
        """HR User of Org A attempting to edit Org B's employee must receive 403 Forbidden."""
        self.client.login(username="hr_user_a", password="password123")
        response = self.client.get(reverse('employees:edit', kwargs={'pk': self.emp_b.pk}))
        self.assertEqual(response.status_code, 403)

    def test_org_a_user_cannot_edit_org_b_department(self):
        """HR User of Org A attempting to edit Org B's department must receive 403 Forbidden."""
        self.client.login(username="hr_user_a", password="password123")
        response = self.client.get(reverse('departments:edit', kwargs={'pk': self.dept_b.pk}))
        self.assertEqual(response.status_code, 403)

    def test_org_a_user_cannot_download_org_b_document(self):
        """HR User of Org A attempting to download private document of Org B employee must receive 403 Forbidden."""
        # Create dummy document for Org B's employee
        test_file = SimpleUploadedFile("confidential.pdf", b"Confidential content", content_type="application/pdf")
        doc_b = EmployeeDocument.objects.create(
            employee=self.emp_b,
            document_name="Offer Letter",
            document_type=DocumentType.JOINING_LETTER,
            file=test_file,
            uploaded_by=self.user_b
        )

        self.client.login(username="hr_user_a", password="password123")
        response = self.client.get(reverse('documents:download', kwargs={'pk': doc_b.pk}))
        self.assertEqual(response.status_code, 403)
