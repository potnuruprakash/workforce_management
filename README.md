# Workforce OS — Employee Details Management System

> **Academic Title:** Employee Details Management System  
> **Architecture:** Production-Grade Multi-Tenant Workforce Management SaaS Platform  
> **Tech Stack:** Python 3.x, Django 5.x/6.x, SQLite (PostgreSQL Ready), Bootstrap 5.3, Vanilla JavaScript, Chart.js

---

## 1. Executive Summary & Overview

**Workforce OS** is a production-grade, multi-tenant Workforce and Staff Management SaaS MVP. Built with clean modular Django architecture, it is designed from the ground up to support any institutional structure—**Colleges, Universities, Companies, Hospitals, Schools, NGOs, and Government Entities**—without altering core business logic or hardcoding organization-specific assumptions.

### Key Highlights
- **Strict Multi-Tenant Isolation:** Data across institutions (e.g. *MVGR College*, *ABC Technologies*, *City Care Hospital*) is partitioned at the backend and QuerySet layer using custom `TenantMiddleware`. Cross-tenant data leaks are strictly prevented and backed by automated unit tests.
- **Role-Based Access Control (RBAC):** Five distinct operational roles:
  1. `Platform Super Admin`: Cross-tenant telemetry and global organization management.
  2. `Organization Owner`: Tenant settings, executive oversight, and user permissions.
  3. `HR / Admin`: Complete staff lifecycle, department operations, and document verification.
  4. `Department Manager`: Departmental staff directory and team performance review.
  5. `Employee / Staff`: Self-service profile, document uploads, and personal notifications.
- **Employee Lifecycle & Preservation:** Supports candidate progression:  
  `Active` &rarr; `On Leave` &rarr; `Resigned` &rarr; `Retired` &rarr; `Terminated` &rarr; `Archived`.  
  Historical staff records and credentials are soft-archived rather than destructively deleted.
- **Secure Document Vault:** Upload, verification, and permission-checked file streaming for resumes, degrees, government IDs, and appointment letters with file-type and size validation (5MB max).
- **Compliance Audit Trail:** Immutable event logging (`CREATE`, `UPDATE`, `ARCHIVE`, `DELETE`, `LOGIN`, `DOCUMENT_UPLOAD`) recording actors, timestamps, entity IDs, and client IP addresses.
- **Interactive Dashboards:** Real-time headcount metrics and dynamic charts rendered via Chart.js.

---

## 2. Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+, Django 5.x / 6.x, Django ORM, Django Built-in Authentication |
| **Database** | SQLite (Zero-config development), Fully compatible with PostgreSQL |
| **Frontend** | HTML5, CSS3, Bootstrap 5.3.3, Bootstrap Icons 1.11.3, Chart.js 4.4.1 |
| **Templating** | Django Server-Rendered Templates with custom Context Processors |
| **Security** | CSRF Protection, Password Hashing (PBKDF2/SHA256), Session-based Auth, File Upload Validators |

---

## 3. System Architecture & Database Models

```
Platform Ecosystem
│
├── Organization (Tenant)
│   ├── Organization Memberships (User <-> Org with RBAC Roles)
│   ├── Departments (Scoped by Organization & Department Code)
│   │   └── Department Head / Manager (Linked to Employee)
│   ├── Employees (Scoped by Org & Employee ID, with Full Lifecycle)
│   │   ├── Documents (Verification status, secure file streaming)
│   │   └── User Account (Optional Self-Service login)
│   ├── Audit Logs (Immutable event stream)
│   └── Notifications (In-app alerts and announcements)
```

### Relational Entity Schema
- **`Organization`**: `id`, `name`, `organization_type` (`COLLEGE`, `COMPANY`, `HOSPITAL`, etc.), `email`, `phone`, `address`, `website`, `description`, `is_active`, `created_at`.
- **`OrganizationMembership`**: `user`, `organization`, `role` (`SUPER_ADMIN`, `OWNER`, `HR_ADMIN`, `MANAGER`, `EMPLOYEE`), `is_default`, `is_active`.
- **`Department`**: `name`, `code`, `organization` (FK), `description`, `manager` (FK Employee, optional), `is_active`.  
  *Constraint:* `unique_together = ('organization', 'code')`.
- **`Employee`**: `employee_id` (unique within organization), `user` (OneToOne, optional), `full_name`, `date_of_birth`, `gender`, `email`, `phone_number`, `address`, `organization` (FK), `department` (FK), `designation`, `qualification`, `bio`, `joining_date`, `employment_status`, `profile_photo`, `is_archived`.  
  *Constraint:* `unique_together = ('organization', 'employee_id')`.
- **`EmployeeDocument`**: `employee` (FK), `document_name`, `document_type`, `file`, `file_size`, `uploaded_by` (FK), `verification_status`, `expiry_date`.
- **`AuditLog`**: `user` (FK), `organization` (FK), `action`, `entity_type`, `entity_id`, `description`, `ip_address`, `timestamp`.
- **`Notification`**: `recipient` (FK), `organization` (FK), `title`, `message`, `notification_type`, `link`, `is_read`.

---

## 4. Project Directory Structure

```
workforce_management/
│
├── manage.py                        # Django execution utility
├── requirements.txt                 # Application dependencies
├── README.md                        # Documentation
│
├── config/                          # Central project configuration
│   ├── settings.py                  # Environment-ready settings (DB, Auth, Static/Media)
│   ├── urls.py                      # Master URL routing & custom error handlers
│   ├── wsgi.py                      # WSGI production gateway
│   └── asgi.py                      # ASGI async gateway
│
├── apps/                            # Modular domain applications
│   ├── core/                        # Middleware, base models, permissions, management commands
│   │   ├── middleware.py            # TenantMiddleware (tenant isolation)
│   │   ├── permissions.py           # RBAC decorators (@org_admin_required, @tenant_required)
│   │   ├── utils.py                 # File upload validator
│   │   └── management/commands/     # load_sample_data.py
│   ├── accounts/                    # Login, logout, user profile, password change, org switcher
│   ├── organizations/               # Tenant CRUD & platform administration
│   ├── departments/                 # Department CRUD with deletion safeguards
│   ├── employees/                   # Employee directory, search, filter, pagination, profile
│   ├── documents/                   # Secure document management and permissioned streaming
│   ├── audit/                       # System compliance and event trail
│   ├── notifications/               # In-app notification center
│   └── dashboard/                   # Dual dashboard (Platform vs Organization Tenant)
│
├── templates/                       # Bootstrap 5 Django templates
│   ├── base.html                    # Layout with sidebar, navbar, switcher, notifications
│   ├── 403.html, 404.html, 500.html # Custom error pages
│   ├── accounts/                    # Login, profile, password change
│   ├── dashboard/                   # Organization & Platform dashboards
│   ├── organizations/               # List, detail, form
│   ├── departments/                 # List, form
│   ├── employees/                   # Directory, profile, form, confirm archive
│   ├── audit/                       # Filterable audit log
│   └── notifications/               # Notification list
│
├── static/
│   ├── css/custom.css               # Clean enterprise SaaS UI styling
│   └── js/main.js                   # Modal hooks, alerts, dynamic interactions
│
├── media/                           # User-uploaded profile photos & verified documents
└── tests/                           # Automated unit & integration tests
    ├── test_tenant_isolation.py     # Multi-tenancy cross-access tests
    ├── test_authentication.py       # Login/logout & session security tests
    ├── test_employee_crud.py        # Referential integrity, archival, and validation tests
    └── test_documents.py            # Secure download permissions and file validation tests
```

---

## 5. Getting Started & Installation (Windows PowerShell)

### Step 1: Open PowerShell and Navigate to Project
```powershell
cd C:\Users\praka\.gemini\antigravity-ide\scratch\workforce_management
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run Database Migrations
```powershell
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Seed Sample Multi-Tenant Data
Run the idempotent sample data generator:
```powershell
python manage.py load_sample_data
```

This automatically sets up **3 diverse institutions** with departments, employees, documents, and credentials:
- **ABC Technologies** (`Company`)
- **MVGR Educational Institution** (`College`)
- **City Care Hospital** (`Hospital`)

### Step 6: Start the Development Server
```powershell
python manage.py runserver
```
Visit **http://127.0.0.1:8000** in your browser.

---

## 6. Pre-Configured Demo Credentials

| Role | Username | Password | Organization / Scope |
|---|---|---|---|
| **Platform Super Admin** | `admin` | `admin123` | Global Platform Overview & All Tenants |
| **Company HR Admin** | `hr_abctech` | `admin123` | ABC Technologies |
| **College HR Admin** | `hr_mvgr` | `admin123` | MVGR Educational Institution |
| **Hospital HR Admin** | `hr_citycare` | `admin123` | City Care Hospital |

*(Note: These credentials are created strictly for local development and demonstration purposes.)*

---

## 7. Creating a Custom Superuser
If you wish to create your own production administrator:
```powershell
python manage.py createsuperuser
```
Follow the prompts for username, email, and password.

---

## 8. Running Automated Tests

The application includes an automated test suite verifying tenant isolation boundaries, authentication, referential constraints, file validation, and document permissions.

Run all tests:
```powershell
python manage.py test tests
```

Expected Output:
```
Creating test database for alias 'default'...
................
----------------------------------------------------------------------
Ran 16 tests in 10.914s

OK
Destroying test database for alias 'default'...
```

---

## 9. Security & Production Deployment Guide

1. **Environment Variables**:
   In production, set the following environment variables:
   - `DJANGO_SECRET_KEY`: A high-entropy cryptographic key.
   - `DJANGO_DEBUG`: Set to `False`.
   - `DJANGO_ALLOWED_HOSTS`: Comma-separated domain names (e.g. `workforce.yourdomain.com`).
   - `DB_ENGINE`: `django.db.backends.postgresql`
   - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

2. **Static & Media Files**:
   - Collect static files for production:
     ```powershell
     python manage.py collectstatic --noinput
     ```
   - WhiteNoise is pre-configured in `settings.py` for efficient static file streaming.
   - Secure private media storage (e.g. AWS S3 or private local storage) should be used for production document uploads.

---

## 10. Future Product Roadmap

- [ ] **Attendance & Time Tracking:** Biometric clock-in integrations, geo-fenced mobile check-ins.
- [ ] **Leave Management:** Custom leave policies (casual, sick, earned), approval workflows, and leave balances.
- [ ] **RESTful API:** Django REST Framework endpoints for mobile apps and third-party HRIS integrations.
- [ ] **Self-Service Onboarding:** Digital onboarding checklists for newly hired candidates.
- [ ] **SaaS Billing & Subscriptions:** Stripe/Razorpay integration for per-seat tenant licensing.
