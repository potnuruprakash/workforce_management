"""
Management command to seed development & demo data.
Creates idempotent Organizations, Departments, Roles, Employees, and Audits.
"""

from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.organizations.models import Organization
from apps.departments.models import Department
from apps.employees.models import Employee, EmploymentStatus, Gender
from apps.accounts.models import OrganizationMembership, Role
from apps.audit.models import AuditLog, AuditAction
from apps.notifications.models import Notification, NotificationType


class Command(BaseCommand):
    help = "Loads realistic sample development data for testing and demonstrations (idempotent)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("===> Seeding Workforce Management Sample Data (Development Only)..."))

        # 1. Superuser
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@workforce.local',
                'first_name': 'Platform',
                'last_name': 'SuperAdmin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("  [+] Created superuser: 'admin' (password: 'admin123')"))
        else:
            self.stdout.write("  [*] Superuser 'admin' already exists.")

        # 2. Organization 1: ABC Technologies (Company)
        abc_org, _ = Organization.objects.get_or_create(
            name='ABC Technologies',
            defaults={
                'organization_type': Organization.TYPE_COMPANY,
                'email': 'contact@abctechnologies.com',
                'phone': '+1 (555) 012-3456',
                'address': 'Tech Park, Sector 4, Silicon Valley, CA 94025',
                'website': 'https://www.abctechnologies.com',
                'description': 'Leading enterprise software development and cloud engineering firm.',
                'is_active': True,
            }
        )

        # 3. Organization 2: MVGR Educational Institution (College)
        mvgr_org, _ = Organization.objects.get_or_create(
            name='MVGR Educational Institution',
            defaults={
                'organization_type': Organization.TYPE_COLLEGE,
                'email': 'admissions@mvgrcollege.edu',
                'phone': '+91 8922 241039',
                'address': 'Vijayaram Nagar Campus, Chintalavalasa, Vizianagaram, AP 535005',
                'website': 'https://www.mvgrce.edu.in',
                'description': 'Premier accredited engineering college offering undergraduate and graduate programs.',
                'is_active': True,
            }
        )

        # 4. Organization 3: City Care Hospital (Hospital)
        hospital_org, _ = Organization.objects.get_or_create(
            name='City Care Hospital',
            defaults={
                'organization_type': Organization.TYPE_HOSPITAL,
                'email': 'helpdesk@citycarehospital.org',
                'phone': '+1 (555) 987-6543',
                'address': '450 Healthcare Boulevard, Metro District, NY 10001',
                'website': 'https://www.citycarehospital.org',
                'description': 'Multi-specialty tertiary care hospital with 24/7 emergency, trauma, and cardiology centers.',
                'is_active': True,
            }
        )

        # User accounts for tenants
        def create_tenant_user(username, email, first_name, last_name, org, role):
            u, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )
            if created:
                u.set_password('admin123')
                u.save()

            OrganizationMembership.objects.get_or_create(
                user=u,
                organization=org,
                defaults={'role': role, 'is_default': True}
            )
            return u

        hr_abc = create_tenant_user('hr_abctech', 'hr@abctech.com', 'David', 'Miller', abc_org, Role.HR_ADMIN)
        owner_abc = create_tenant_user('owner_abctech', 'ceo@abctech.com', 'Alex', 'Chen', abc_org, Role.OWNER)

        hr_mvgr = create_tenant_user('hr_mvgr', 'registrar@mvgr.edu', 'Suresh', 'Babu', mvgr_org, Role.HR_ADMIN)
        owner_mvgr = create_tenant_user('owner_mvgr', 'principal@mvgr.edu', 'Dr. Mohan', 'Rao', mvgr_org, Role.OWNER)

        hr_citycare = create_tenant_user('hr_citycare', 'hr@citycare.org', 'Sarah', 'Jenkins', hospital_org, Role.HR_ADMIN)

        # Departments
        # ABC Tech
        dept_dev, _ = Department.objects.get_or_create(organization=abc_org, code='DEV', defaults={'name': 'Software Engineering', 'description': 'Full-stack software and architecture'})
        dept_qa, _ = Department.objects.get_or_create(organization=abc_org, code='QA', defaults={'name': 'Quality Assurance', 'description': 'Automated and manual testing'})
        dept_hr, _ = Department.objects.get_or_create(organization=abc_org, code='HR', defaults={'name': 'Human Resources', 'description': 'Talent acquisition and employee relations'})
        dept_fin, _ = Department.objects.get_or_create(organization=abc_org, code='FIN', defaults={'name': 'Finance & Accounting', 'description': 'Financial planning and payroll'})

        # MVGR College
        dept_cse, _ = Department.objects.get_or_create(organization=mvgr_org, code='CSE', defaults={'name': 'Computer Science & Engineering', 'description': 'CS, AI, and data science research'})
        dept_ece, _ = Department.objects.get_or_create(organization=mvgr_org, code='ECE', defaults={'name': 'Electronics & Communication', 'description': 'VLSI and embedded systems'})
        dept_mech, _ = Department.objects.get_or_create(organization=mvgr_org, code='MECH', defaults={'name': 'Mechanical Engineering', 'description': 'Robotics, thermal and fluid dynamics'})
        dept_admin, _ = Department.objects.get_or_create(organization=mvgr_org, code='ADMIN', defaults={'name': 'College Administration', 'description': 'Admissions, examinations and student affairs'})

        # City Care Hospital
        dept_card, _ = Department.objects.get_or_create(organization=hospital_org, code='CARD', defaults={'name': 'Cardiology & Critical Care', 'description': 'Advanced cardiovascular treatments'})
        dept_emerg, _ = Department.objects.get_or_create(organization=hospital_org, code='EMERG', defaults={'name': 'Emergency & Trauma', 'description': '24/7 acute trauma and resuscitation'})
        dept_nurs, _ = Department.objects.get_or_create(organization=hospital_org, code='NURS', defaults={'name': 'Nursing Services', 'description': 'Inpatient and outpatient bedside nursing'})
        dept_hosp_admin, _ = Department.objects.get_or_create(organization=hospital_org, code='ADMIN', defaults={'name': 'Hospital Operations', 'description': 'Hospital facilities, logistics and billing'})

        # Helper to create employee
        def create_employee(org, dept, emp_id, full_name, dob, gender, email, phone, address, designation, qual, bio, joining, status):
            emp, created = Employee.objects.get_or_create(
                organization=org,
                employee_id=emp_id,
                defaults={
                    'department': dept,
                    'full_name': full_name,
                    'date_of_birth': dob,
                    'gender': gender,
                    'email': email,
                    'phone_number': phone,
                    'address': address,
                    'designation': designation,
                    'qualification': qual,
                    'bio': bio,
                    'joining_date': joining,
                    'employment_status': status,
                }
            )
            return emp

        # ABC Tech Employees
        e1 = create_employee(abc_org, dept_dev, 'EMP-101', 'Rajesh Sharma', date(1988, 4, 12), Gender.MALE, 'rajesh.sharma@abctech.com', '+1 555-0101', '102 Tech Lane, San Jose, CA', 'VP of Engineering', 'M.Tech in CSE', 'Over 14 years of engineering leadership in high-scale SaaS architectures.', date(2019, 3, 1), EmploymentStatus.ACTIVE)
        e2 = create_employee(abc_org, dept_dev, 'EMP-102', 'Priya Nair', date(1993, 8, 24), Gender.FEMALE, 'priya.nair@abctech.com', '+1 555-0102', '45 Willow Ave, Sunnyvale, CA', 'Lead Software Engineer', 'B.Tech in IT', 'Full stack specialist passionate about distributed backend systems and Python.', date(2021, 6, 15), EmploymentStatus.ACTIVE)
        e3 = create_employee(abc_org, dept_qa, 'EMP-103', 'Vikram Malhotra', date(1991, 11, 5), Gender.MALE, 'vikram.m@abctech.com', '+1 555-0103', '88 Redwood Blvd, Mountain View, CA', 'Senior QA Automation Engineer', 'MCA in Computer Applications', 'Focuses on end-to-end automated testing pipelines and performance benchmarks.', date(2022, 1, 10), EmploymentStatus.ACTIVE)
        e4 = create_employee(abc_org, dept_hr, 'EMP-104', 'Ananya Roy', date(1995, 2, 18), Gender.FEMALE, 'ananya.roy@abctech.com', '+1 555-0104', '310 Pine St, Palo Alto, CA', 'HR Operations Specialist', 'MBA in Human Resources', 'Oversees talent acquisition, onboarding workflows, and workplace culture.', date(2023, 4, 1), EmploymentStatus.ACTIVE)
        e5 = create_employee(abc_org, dept_fin, 'EMP-105', 'Rohan Gupta', date(1990, 7, 30), Gender.MALE, 'rohan.gupta@abctech.com', '+1 555-0105', '120 Market St, San Francisco, CA', 'Financial Analyst', 'Chartered Accountant (CA)', 'Manages corporate financial modeling, tax reporting, and payroll audits.', date(2020, 9, 1), EmploymentStatus.ACTIVE)
        e6 = create_employee(abc_org, dept_dev, 'EMP-106', 'Sneha Reddy', date(1996, 5, 14), Gender.FEMALE, 'sneha.reddy@abctech.com', '+1 555-0106', '77 Mission St, San Francisco, CA', 'Frontend UI Engineer', 'B.Tech in CS', 'Expert in modern JavaScript, responsive interfaces, and accessible design.', date(2024, 1, 15), EmploymentStatus.ON_LEAVE)

        # Set manager for DEV
        dept_dev.manager = e1
        dept_dev.save()

        # MVGR College Staff
        f1 = create_employee(mvgr_org, dept_cse, 'FAC-201', 'Dr. K. V. Satyanarayana', date(1975, 6, 15), Gender.MALE, 'kvs@mvgr.edu', '+91 98480 12345', 'Staff Quarters Q4, MVGR Campus, Vizianagaram', 'Professor & HOD', 'Ph.D in Artificial Intelligence', 'Senior academician with 25+ published research papers in neural networks and algorithms.', date(2008, 7, 1), EmploymentStatus.ACTIVE)
        f2 = create_employee(mvgr_org, dept_ece, 'FAC-202', 'Dr. Sunita Rao', date(1982, 3, 20), Gender.FEMALE, 'sunita.rao@mvgr.edu', '+91 98480 54321', 'Plot 14, Cantonment Area, Vizianagaram', 'Associate Professor', 'Ph.D in VLSI Systems', 'Conducts research in low-power digital architecture and CMOS fabrication.', date(2014, 8, 1), EmploymentStatus.ACTIVE)
        f3 = create_employee(mvgr_org, dept_mech, 'FAC-203', 'Ramesh Varma', date(1987, 9, 10), Gender.MALE, 'ramesh.v@mvgr.edu', '+91 98480 67890', 'Door 4-12, Phool Bagh, Vizianagaram', 'Assistant Professor', 'M.Tech in Machine Design', 'Faculty advisor for SAE collegiate design competitions and robotics.', date(2017, 11, 15), EmploymentStatus.ACTIVE)
        f4 = create_employee(mvgr_org, dept_cse, 'FAC-204', 'Kavita Deshmukh', date(1992, 12, 1), Gender.FEMALE, 'kavita.d@mvgr.edu', '+91 98480 99887', 'Flat 202, Green View Apartments, Vizianagaram', 'Assistant Professor', 'M.Tech in Software Engineering', 'Teaches database systems, web programming, and cloud computing.', date(2022, 6, 1), EmploymentStatus.ACTIVE)
        f5 = create_employee(mvgr_org, dept_admin, 'FAC-205', 'M. Narayana', date(1970, 1, 12), Gender.MALE, 'narayana@mvgr.edu', '+91 98480 11223', 'Staff Colony, Vizianagaram', 'Administrative Officer', 'Master of Arts (MA)', 'Oversees academic records, regulatory accreditations, and admissions.', date(2002, 5, 1), EmploymentStatus.ACTIVE)

        dept_cse.manager = f1
        dept_cse.save()

        # City Care Hospital Staff
        h1 = create_employee(hospital_org, dept_card, 'DOC-301', 'Dr. Arvind Swaminathan', date(1972, 8, 8), Gender.MALE, 'arvind.s@citycare.org', '+1 555-9001', '72 Park Ave, New York, NY', 'Chief Cardiologist', 'MBBS, MD, DM (Cardiology)', 'Renowned interventional cardiologist with over 20 years clinical experience.', date(2015, 4, 1), EmploymentStatus.ACTIVE)
        h2 = create_employee(hospital_org, dept_emerg, 'DOC-302', 'Dr. Meera Krishnan', date(1985, 10, 18), Gender.FEMALE, 'meera.k@citycare.org', '+1 555-9002', '140 East 45th St, New York, NY', 'Emergency Specialist', 'MBBS, MD (Emergency Medicine)', 'Head of Emergency & Resuscitation Center, ACLS and ATLS certified.', date(2018, 9, 1), EmploymentStatus.ACTIVE)
        h3 = create_employee(hospital_org, dept_nurs, 'NUR-303', 'Sister Mary Joseph', date(1978, 4, 25), Gender.FEMALE, 'mary.j@citycare.org', '+1 555-9003', '85 Lexington Ave, New York, NY', 'Head Nursing Supervisor', 'B.Sc in Nursing, M.Sc', 'Directs nursing clinical standards, patient safety protocols, and staffing rosters.', date(2012, 2, 1), EmploymentStatus.ACTIVE)
        h4 = create_employee(hospital_org, dept_nurs, 'NUR-304', 'Anita Thomas', date(1994, 7, 14), Gender.FEMALE, 'anita.t@citycare.org', '+1 555-9004', '200 Queens Blvd, Queens, NY', 'Staff Nurse ICU', 'GNM & B.Sc Nursing', 'Specialized in intensive cardiac care and post-operative monitoring.', date(2021, 3, 15), EmploymentStatus.ACTIVE)
        h5 = create_employee(hospital_org, dept_hosp_admin, 'ADM-305', 'David Wilson', date(1980, 5, 29), Gender.MALE, 'david.w@citycare.org', '+1 555-9005', '33 Madison Ave, New York, NY', 'Hospital Operations Manager', 'MHA (Hospital Administration)', 'Responsible for biomedical equipment logistics, procurement, and patient services.', date(2016, 11, 1), EmploymentStatus.ACTIVE)

        dept_card.manager = h1
        dept_card.save()

        # Sample Notifications
        Notification.objects.get_or_create(
            recipient=admin_user,
            title="System Ready",
            defaults={
                'message': "Workforce Management SaaS platform initialized with sample multi-tenant data.",
                'notification_type': NotificationType.SUCCESS,
                'link': '/platform/'
            }
        )
        Notification.objects.get_or_create(
            recipient=hr_abc,
            organization=abc_org,
            title="New Staff Onboarding Completed",
            defaults={
                'message': "Employee Priya Nair (EMP-102) has completed document verification.",
                'notification_type': NotificationType.INFO,
                'link': f'/employees/{e2.pk}/'
            }
        )

        # Sample Audit Logs
        AuditLog.objects.get_or_create(
            organization=abc_org,
            user=hr_abc,
            action=AuditAction.CREATE,
            entity_type='Employee',
            entity_id=str(e2.pk),
            defaults={
                'description': f"HR Admin onboarded employee Priya Nair ({e2.employee_id}) into Software Engineering.",
                'ip_address': '127.0.0.1'
            }
        )
        AuditLog.objects.get_or_create(
            organization=mvgr_org,
            user=hr_mvgr,
            action=AuditAction.CREATE,
            entity_type='Department',
            entity_id=str(dept_cse.pk),
            defaults={
                'description': "Created Department Computer Science & Engineering (CSE).",
                'ip_address': '127.0.0.1'
            }
        )

        self.stdout.write(self.style.SUCCESS("===> Sample Data successfully loaded!"))
        self.stdout.write(self.style.SUCCESS("""
---------------------------------------------------------------------
DEV & DEMO CREDENTIALS (Idempotent):
- Platform Super Admin:  Username: admin       | Password: admin123
- ABC Tech HR:           Username: hr_abctech  | Password: admin123
- MVGR College HR:       Username: hr_mvgr     | Password: admin123
- City Care Hospital HR: Username: hr_citycare | Password: admin123
---------------------------------------------------------------------
"""))
