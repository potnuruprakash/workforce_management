"""
URL routing for documents application.
"""

from django.urls import path
from apps.documents import views

app_name = 'documents'

urlpatterns = [
    path('upload/<int:employee_pk>/', views.document_upload, name='upload'),
    path('<int:pk>/download/', views.document_download, name='download'),
    path('<int:pk>/verify/', views.document_verify, name='verify'),
    path('<int:pk>/delete/', views.document_delete, name='delete'),
]
