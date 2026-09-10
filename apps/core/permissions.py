"""
Role-based and tenant-aware permission decorators and mixins.
"""

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.accounts.models import Role


def super_admin_required(view_func):
    """Decorator requiring the user to be a Platform Super Admin."""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or getattr(request, 'active_role', None) == Role.SUPER_ADMIN:
            return view_func(request, *args, **kwargs)
        messages.error(request, "Access denied: Platform Administrator privileges required.")
        raise PermissionDenied("Platform Super Admin access required.")
    return _wrapped_view


def org_admin_required(view_func):
    """Decorator requiring Organization Owner or HR/Admin role."""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        role = getattr(request, 'active_role', None)
        if role in (Role.OWNER, Role.HR_ADMIN):
            return view_func(request, *args, **kwargs)
        messages.error(request, "Access denied: Organization Admin or HR privileges required.")
        raise PermissionDenied("Organization Admin access required.")
    return _wrapped_view


def manager_required(view_func):
    """Decorator requiring Manager, HR/Admin, or Owner role."""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        role = getattr(request, 'active_role', None)
        if role in (Role.OWNER, Role.HR_ADMIN, Role.MANAGER):
            return view_func(request, *args, **kwargs)
        messages.error(request, "Access denied: Managerial or Administrative privileges required.")
        raise PermissionDenied("Manager access required.")
    return _wrapped_view


def tenant_required(view_func):
    """Ensures an active organization context is present."""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not getattr(request, 'active_organization', None):
            if request.user.is_superuser:
                return redirect('dashboard:platform')
            messages.warning(request, "No active organization assigned to your account. Please contact an administrator.")
            return redirect('accounts:profile')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
