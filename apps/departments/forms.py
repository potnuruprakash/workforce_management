"""
Forms for Department management.
"""

from django import forms
from apps.departments.models import Department
from apps.employees.models import Employee


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'manager', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Computer Science, Cardiology, HR'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CSE, CARD, HR'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Scope or mission of department'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        if organization:
            # Filter manager dropdown strictly to active employees of this organization
            self.fields['manager'].queryset = Employee.objects.filter(
                organization=organization,
                is_archived=False
            ).order_by('full_name')
        else:
            self.fields['manager'].queryset = Employee.objects.none()

        self.fields['manager'].empty_label = "-- Select Department Manager (Optional) --"
