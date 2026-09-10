"""
Automated tests for Employee model validations, referential integrity, and archiving.
"""

from datetime import date
from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.urls import reverse

from apps.organizations.models import Organization
from apps.departments.models import Department
from apps.employees.models import Employee, EmploymentStatus, Gender
from apps.accounts.models import OrganizationMembership, Role


class EmployeeModelTests(TestCase):
    def setUp(self):
        self.org1 = Organization.objects.create(
            name="Org One",
            organization_type=Organization.TYPE_COMPANY,
            email="one@org.com",
            phone="111",
            address="One St"
        )
        self.org2 = Organization.objects.create(
            name="Org Two",
            organization_type=Organization.TYPE_COLLEGE,
            email="two@org.com",
            phone="222",
            address="Two St"
        )

        self.dept_org1 = Department.objects.create(
            organization=self.org1,
            name="Org1 Tech",
            code="TECH"
        )
        self.dept_org2 = Department.objects.create(
            organization=self.org2,
            name="Org2 Science",
            code="SCI"
        )

        self.hr_user = User.objects.create_user(
            username="hr1",
            email="hr1@org.com",
            password="password123"
        )
        OrganizationMembership.objects.create(
            user=self.hr_user,
            organization=self.org1,
            role=Role.HR_ADMIN,
            is_default=True
        )

    def test_department_mismatch_raises_validation_error(self):
        """Assigning a department from Org 2 to an employee in Org 1 must raise a ValidationError."""
        emp = Employee(
            organization=self.org1,
            department=self.dept_org2,  # Belongs to Org 2!
            employee_id="MISMATCH-1",
            full_name="Invalid Assignment",
            date_of_birth=date(1990, 1, 1),
            gender=Gender.MALE,
            email="invalid@org.com",
            phone_number="123",
            address="Address",
            designation="Dev",
            qualification="B.Tech",
            joining_date=date(2023, 1, 1),
            employment_status=EmploymentStatus.ACTIVE
        )
        with self.assertRaises(ValidationError):
            emp.full_clean()

    def test_same_employee_id_allowed_in_different_organizations(self):
        """Employee ID 'EMP-100' should be allowed in Org 1 AND Org 2 independently."""
        emp1 = Employee.objects.create(
            organization=self.org1,
            department=self.dept_org1,
            employee_id="EMP-100",
            full_name="Employee One",
            date_of_birth=date(1990, 1, 1),
            gender=Gender.MALE,
            email="emp1@org.com",
            phone_number="111",
            address="Address 1",
            designation="Dev",
            qualification="B.Tech",
            joining_date=date(2023, 1, 1),
            employment_status=EmploymentStatus.ACTIVE
        )
        emp2 = Employee.objects.create(
            organization=self.org2,
            department=self.dept_org2,
            employee_id="EMP-100",  # Same ID, different org!
            full_name="Employee Two",
            date_of_birth=date(1992, 2, 2),
            gender=Gender.FEMALE,
            email="emp2@org.com",
            phone_number="222",
            address="Address 2",
            designation="Lecturer",
            qualification="M.Tech",
            joining_date=date(2023, 2, 1),
            employment_status=EmploymentStatus.ACTIVE
        )
        self.assertIsNotNone(emp1.pk)
        self.assertIsNotNone(emp2.pk)
        self.assertEqual(emp1.employee_id, emp2.employee_id)

    def test_soft_archiving_and_restore(self):
        """Archiving sets is_archived to True; restoring returns to active."""
        emp = Employee.objects.create(
            organization=self.org1,
            department=self.dept_org1,
            employee_id="ARCH-1",
            full_name="Archived Staff",
            date_of_birth=date(1988, 3, 3),
            gender=Gender.MALE,
            email="arch@org.com",
            phone_number="333",
            address="Address",
            designation="Consultant",
            qualification="MBA",
            joining_date=date(2021, 1, 1),
            employment_status=EmploymentStatus.ACTIVE
        )
        self.assertFalse(emp.is_archived)

        emp.archive()
        emp.refresh_from_db()
        self.assertTrue(emp.is_archived)
        self.assertIsNotNone(emp.archived_at)

        emp.restore()
        emp.refresh_from_db()
        self.assertFalse(emp.is_archived)
        self.assertIsNone(emp.archived_at)

    def test_department_deletion_blocked_when_employees_exist(self):
        """Cannot delete department if employees are assigned to it."""
        Employee.objects.create(
            organization=self.org1,
            department=self.dept_org1,
            employee_id="LINKED-1",
            full_name="Linked Staff",
            date_of_birth=date(1989, 4, 4),
            gender=Gender.FEMALE,
            email="linked@org.com",
            phone_number="444",
            address="Address",
            designation="Dev",
            qualification="B.Tech",
            joining_date=date(2022, 1, 1),
            employment_status=EmploymentStatus.ACTIVE
        )

        client = Client()
        client.login(username="hr1", password="password123")
        response = self.client.post(reverse('departments:delete', kwargs={'pk': self.dept_org1.pk}))
        # Department must still exist in DB
        self.assertTrue(Department.objects.filter(pk=self.dept_org1.pk).exists())
