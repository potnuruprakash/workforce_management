"""
URL routing for organizations application.
"""

from django.urls import path
from apps.organizations import views

app_name = 'organizations'

urlpatterns = [
    path('', views.organization_list, name='list'),
    path('create/', views.organization_create, name='create'),
    path('<int:pk>/', views.organization_detail, name='detail'),
    path('<int:pk>/edit/', views.organization_update, name='edit'),
]
