"""
URL routing for employees application.
"""

from django.urls import path
from apps.employees import views

app_name = 'employees'

urlpatterns = [
    path('', views.employee_list, name='list'),
    path('create/', views.employee_create, name='create'),
    path('<int:pk>/', views.employee_detail, name='detail'),
    path('<int:pk>/edit/', views.employee_update, name='edit'),
    path('<int:pk>/archive/', views.employee_archive, name='archive'),
    path('<int:pk>/restore/', views.employee_restore, name='restore'),
    path('<int:pk>/delete/', views.employee_delete, name='delete'),
]
