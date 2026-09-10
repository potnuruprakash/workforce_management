"""
Views for secure employee document management and downloads.
"""

import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from apps.documents.models import EmployeeDocument, VerificationStatus
from apps.documents.forms import EmployeeDocumentForm
from apps.employees.models import Employee
from apps.accounts.models import Role
from apps.core.permissions import tenant_required, org_admin_required
from apps.audit.services import log_action
from apps.audit.models import AuditAction


@tenant_required
def document_upload(request, employee_pk):
    """
    Uploads a document to the specified employee's profile.
    """
    org = request.active_organization
    employee = get_object_or_404(Employee, pk=employee_pk)

    # Tenant boundary enforcement
    if employee.organization_id != org.id and not request.user.is_superuser:
        messages.error(request, "Access denied: Cannot upload documents to another organization's employee.")
        raise PermissionDenied("Tenant boundary violation.")

    # Permissions: Employee can upload to own profile; HR/Admin/Manager can upload for staff
    is_self = employee.user == request.user
    role = getattr(request, 'active_role', None)
    can_upload = request.user.is_superuser or is_self or role in (Role.OWNER, Role.HR_ADMIN, Role.MANAGER)

    if not can_upload:
        messages.error(request, "Access denied: You are not authorized to upload documents for this employee.")
        raise PermissionDenied("Insufficient upload permissions.")

    if request.method == 'POST':
        form = EmployeeDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.employee = employee
            doc.uploaded_by = request.user
            doc.save()

            log_action(
                request,
                action=AuditAction.DOCUMENT_UPLOAD,
                entity_type='EmployeeDocument',
                entity_id=doc.pk,
                description=f"Uploaded document '{doc.document_name}' for employee {employee.full_name} ({employee.employee_id})."
            )
            messages.success(request, f"Document '{doc.document_name}' uploaded successfully.")
            return redirect('employees:detail', pk=employee.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
            return redirect('employees:detail', pk=employee.pk)

    return redirect('employees:detail', pk=employee.pk)


@tenant_required
def document_download(request, pk):
    """
    Secure file streaming.
    Ensures that only authorized personnel and the employee can download the document.
    """
    org = request.active_organization
    doc = get_object_or_404(EmployeeDocument.objects.select_related('employee', 'employee__organization', 'employee__department'), pk=pk)

    # 1. Tenant boundary check
    if doc.employee.organization_id != org.id and not request.user.is_superuser:
        messages.error(request, "Access denied: Document belongs to another organization.")
        raise PermissionDenied("Tenant boundary violation.")

    # 2. Role and ownership authorization check
    is_self = doc.employee.user == request.user
    is_admin = request.user.is_superuser or getattr(request, 'active_role', None) in (Role.OWNER, Role.HR_ADMIN)
    is_dept_manager = (
        getattr(request, 'active_role', None) == Role.MANAGER and
        doc.employee.department.manager and
        doc.employee.department.manager.user == request.user
    )

    if not (is_self or is_admin or is_dept_manager):
        messages.error(request, "Access denied: You do not have permission to view or download this private document.")
        raise PermissionDenied("Document access forbidden.")

    if not doc.file or not os.path.exists(doc.file.path):
        raise Http404("Document file was not found on the server.")

    # Stream response
    response = FileResponse(open(doc.file.path, 'rb'))
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(doc.file.name)}"'
    return response


@org_admin_required
@tenant_required
def document_verify(request, pk):
    """
    Updates document verification status (Pending -> Verified or Rejected).
    """
    org = request.active_organization
    doc = get_object_or_404(EmployeeDocument.objects.select_related('employee'), pk=pk)

    if doc.employee.organization_id != org.id and not request.user.is_superuser:
        messages.error(request, "Access denied: Tenant boundary violation.")
        raise PermissionDenied("Tenant boundary violation.")

    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '').strip()

        if new_status in (VerificationStatus.VERIFIED, VerificationStatus.REJECTED, VerificationStatus.PENDING):
            doc.verification_status = new_status
            if notes:
                doc.notes = notes
            doc.save(update_fields=['verification_status', 'notes', 'updated_at'])

            log_action(
                request,
                action=AuditAction.DOCUMENT_VERIFY,
                entity_type='EmployeeDocument',
                entity_id=doc.pk,
                description=f"Changed verification status of document '{doc.document_name}' to {new_status}."
            )
            messages.success(request, f"Document '{doc.document_name}' marked as {doc.get_verification_status_display()}.")

    return redirect('employees:detail', pk=doc.employee.pk)


@tenant_required
def document_delete(request, pk):
    """
    Deletes an employee document.
    """
    org = request.active_organization
    doc = get_object_or_404(EmployeeDocument.objects.select_related('employee'), pk=pk)

    if doc.employee.organization_id != org.id and not request.user.is_superuser:
        messages.error(request, "Access denied: Tenant boundary violation.")
        raise PermissionDenied("Tenant boundary violation.")

    is_admin = request.user.is_superuser or getattr(request, 'active_role', None) in (Role.OWNER, Role.HR_ADMIN)
    is_uploader = doc.uploaded_by == request.user

    if not (is_admin or is_uploader):
        messages.error(request, "Access denied: Only admins or the uploader can delete this document.")
        raise PermissionDenied("Insufficient deletion permissions.")

    if request.method == 'POST':
        employee_id = doc.employee.pk
        doc_name = doc.document_name

        if doc.file and os.path.exists(doc.file.path):
            try:
                os.remove(doc.file.path)
            except OSError:
                pass

        doc.delete()
        log_action(
            request,
            action=AuditAction.DELETE,
            entity_type='EmployeeDocument',
            entity_id=pk,
            description=f"Deleted document '{doc_name}' from employee record."
        )
        messages.success(request, f"Document '{doc_name}' was removed successfully.")
        return redirect('employees:detail', pk=employee_id)

    return redirect('employees:detail', pk=doc.employee.pk)
