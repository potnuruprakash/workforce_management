"""
Forms for employee document upload and verification.
"""

from django import forms
from apps.documents.models import EmployeeDocument, DocumentType
from apps.core.utils import validate_file_upload


class EmployeeDocumentForm(forms.ModelForm):
    expiry_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = EmployeeDocument
        fields = ['document_name', 'document_type', 'file', 'expiry_date', 'notes']
        widgets = {
            'document_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Master Degree Certificate, ID Card'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional remarks or document details'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            validate_file_upload(file)
        return file
