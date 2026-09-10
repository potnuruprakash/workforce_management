/**
 * WORKFORCE OS — CLIENT-SIDE INTERACTIONS & TOUCH ENGINE
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Tooltips Initialization
    const tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltips.forEach(function (el) {
        new bootstrap.Tooltip(el, { boundary: document.body });
    });

    // 2. Universal Action Confirmation Modal Hook
    const actionModalEl = document.getElementById('actionConfirmModal');
    if (actionModalEl) {
        actionModalEl.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            if (!button) return;

            const actionUrl = button.getAttribute('data-action-url') || '';
            const actionTitle = button.getAttribute('data-action-title') || 'Confirm Action';
            const actionMessage = button.getAttribute('data-action-message') || 'Are you sure you want to proceed?';
            const actionBtnText = button.getAttribute('data-action-btn-text') || 'Confirm';
            const actionBtnClass = button.getAttribute('data-action-btn-class') || 'btn-danger';

            const form = actionModalEl.querySelector('#actionConfirmForm');
            const titleEl = actionModalEl.querySelector('#actionModalTitle');
            const messageEl = actionModalEl.querySelector('#actionModalMessage');
            const submitBtn = actionModalEl.querySelector('#actionModalSubmitBtn');

            if (form) form.action = actionUrl;
            if (titleEl) titleEl.textContent = actionTitle;
            if (messageEl) messageEl.innerHTML = actionMessage;
            if (submitBtn) {
                submitBtn.textContent = actionBtnText;
                submitBtn.className = 'btn ' + actionBtnClass;
            }
        });
    }

    // 3. Floating Toasts Auto-Dismiss
    const toastElements = document.querySelectorAll('.saas-toast');
    toastElements.forEach(function (toast) {
        setTimeout(function () {
            toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(function () {
                toast.remove();
            }, 300);
        }, 5000);
    });

    // 4. Password Visibility Toggle
    const passwordToggleBtns = document.querySelectorAll('.password-toggle-btn');
    passwordToggleBtns.forEach(function (btn) {
        btn.addEventListener('click', function () {
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);
            const icon = this.querySelector('i');
            if (input) {
                if (input.type === 'password') {
                    input.type = 'text';
                    if (icon) {
                        icon.classList.remove('bi-eye');
                        icon.classList.add('bi-eye-slash');
                    }
                } else {
                    input.type = 'password';
                    if (icon) {
                        icon.classList.remove('bi-eye-slash');
                        icon.classList.add('bi-eye');
                    }
                }
            }
        });
    });

    // 5. Mobile Drawer Auto-Close on Navigation Click
    const drawerEl = document.getElementById('mobileDrawer');
    if (drawerEl) {
        const drawerLinks = drawerEl.querySelectorAll('.sidebar-link');
        drawerLinks.forEach(function (link) {
            link.addEventListener('click', function () {
                const offcanvasInstance = bootstrap.Offcanvas.getInstance(drawerEl);
                if (offcanvasInstance) {
                    offcanvasInstance.hide();
                }
            });
        });
    }
});
