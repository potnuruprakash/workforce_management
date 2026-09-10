"""
URL routing for dashboard application.
"""

from django.urls import path
from apps.dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_index, name='index'),
    path('platform/', views.platform_dashboard, name='platform'),
]
