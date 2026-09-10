"""
Core error views for custom 403, 404, and 500 pages.
"""

from django.shortcuts import render


def custom_permission_denied(request, exception=None):
    return render(request, '403.html', {'message': str(exception) if exception else None}, status=403)


def custom_page_not_found(request, exception=None):
    return render(request, '404.html', {'message': str(exception) if exception else None}, status=404)


def custom_server_error(request):
    return render(request, '500.html', status=500)
