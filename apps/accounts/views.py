"""
Authentication and account management views.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy

from apps.accounts.forms import BootstrapLoginForm, UserProfileForm
from apps.accounts.models import OrganizationMembership, Role
from apps.organizations.models import Organization
from apps.audit.services import log_action
from apps.audit.models import AuditAction


class CustomLoginView(LoginView):
    """
    SaaS authentication view with custom Bootstrap layout and audit trail.
    """
    form_class = BootstrapLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        # Auto-ensure demo accounts exist if platform has not seeded yet
        self._ensure_demo_accounts()
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _ensure_demo_accounts():
        from django.contrib.auth.models import User
        if not User.objects.filter(username='admin').exists():
            try:
                from django.core.management import call_command
                call_command('load_sample_data')
            except Exception:
                pass

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        log_action(
            self.request,
            action=AuditAction.LOGIN,
            entity_type='User',
            entity_id=user.pk,
            description=f"User {user.username} logged in successfully."
        )
        messages.success(self.request, f"Welcome back, {user.first_name or user.username}!")
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        username = (self.request.POST.get('username') or '').strip()
        if username in ('admin', 'hr_abctech', 'hr_mvgr', 'hr_citycare'):
            try:
                from django.core.management import call_command
                call_command('load_sample_data')
            except Exception:
                pass
        messages.error(self.request, "Invalid username or password. Please check your credentials.")
        return super().form_invalid(form)


@login_required
def custom_logout_view(request):
    """
    Handles user logout with audit trail.
    """
    username = request.user.username
    log_action(
        request,
        action=AuditAction.LOGOUT,
        entity_type='User',
        entity_id=request.user.pk,
        description=f"User {username} logged out."
    )
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('accounts:login')


@login_required
def switch_organization(request, org_id):
    """
    Switches active organization context in session.
    Validates that the user has a valid active membership in target organization (or is superuser).
    """
    if request.user.is_superuser:
        org = get_object_or_404(Organization, pk=org_id, is_active=True)
        request.session['active_organization_id'] = org.id
        messages.success(request, f"Switched context to {org.name}.")
    else:
        membership = get_object_or_404(
            OrganizationMembership,
            user=request.user,
            organization_id=org_id,
            is_active=True,
            organization__is_active=True
        )
        request.session['active_organization_id'] = membership.organization_id
        messages.success(request, f"Switched to {membership.organization.name} as {membership.get_role_display()}.")

    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse_lazy('dashboard:index')
    return redirect(next_url)


@login_required
def profile_view(request):
    """
    User account profile page showing user info, memberships, and role assignments.
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            log_action(
                request,
                action=AuditAction.UPDATE,
                entity_type='User',
                entity_id=request.user.pk,
                description=f"User {request.user.username} updated profile details."
            )
            messages.success(request, "Profile updated successfully.")
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    memberships = OrganizationMembership.objects.filter(
        user=request.user
    ).select_related('organization').order_by('-is_default', 'organization__name')

    # If user is linked to an employee profile, fetch it
    employee_profile = getattr(request.user, 'employee_profile', None)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'memberships': memberships,
        'employee_profile': employee_profile,
    })


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed successfully.")
        return super().form_valid(form)
