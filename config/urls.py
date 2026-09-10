"""
Global URL configuration for Workforce Management SaaS Platform.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Built-in Django administrative portal
    path('admin/', admin.site.urls),

    # Modular application routes
    path('', include('apps.dashboard.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('organizations/', include('apps.organizations.urls')),
    path('departments/', include('apps.departments.urls')),
    path('employees/', include('apps.employees.urls')),
    path('documents/', include('apps.documents.urls')),
    path('audit/', include('apps.audit.urls')),
    path('notifications/', include('apps.notifications.urls')),
]

# Development static & media file routing
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler403 = 'apps.core.views.custom_permission_denied'
handler404 = 'apps.core.views.custom_page_not_found'
handler500 = 'apps.core.views.custom_server_error'
