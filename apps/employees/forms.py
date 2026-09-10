"""
Forms for Employee CRUD and profile management.
"""

from django import forms
from django.core.exceptions import ValidationError
from apps.employees.models import Employee, EmploymentStatus, Gender
from apps.departments.models import Department


class EmployeeForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Format: YYYY-MM-DD"
    )
    joining_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Format: YYYY-MM-DD"
    )

    class Meta:
        model = Employee
        fields = [
            'employee_id',
            'full_name',
            'date_of_birth',
            'gender',
            'email',
            'phone_number',
            'address',
            'department',
            'designation',
            'qualification',
            'bio',
            'joining_date',
            'employment_status',
            'profile_photo',
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. EMP-101, FAC-202, DR-301'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full legal or official name'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'employee@organization.com'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 555-0143'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Residential address'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Software Engineer, Professor, Specialist'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. B.Tech in CSE, Ph.D, MBBS, MD'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief professional summary'}),
            'employment_status': forms.Select(attrs={'class': 'form-select'}),
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization

        if organization:
            # Strictly scope department dropdown to active organization's departments
            self.fields['department'].queryset = Department.objects.filter(
                organization=organization,
                is_active=True
            ).order_by('name')
        else:
            self.fields['department'].queryset = Department.objects.none()

        self.fields['department'].empty_label = "-- Select Department --"

    def clean_employee_id(self):
        emp_id = self.cleaned_data.get('employee_id', '').strip()
        if not emp_id:
            raise ValidationError("Employee ID is required.")

        qs = Employee.objects.filter(
            organization=self.organization,
            employee_id__iexact=emp_id
        )
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError(f"Employee ID '{emp_id}' is already assigned to another employee in this organization.")

        return emp_id

    def clean(self):
        cleaned_data = super().clean()
        dob = cleaned_data.get('date_of_birth')
        joining = cleaned_data.get('joining_date')

        if dob and joining and joining <= dob:
            raise ValidationError({'joining_date': "Joining date must be after Date of Birth."})

        dept = cleaned_data.get('department')
        if dept and self.organization and dept.organization_id != self.organization.id:
            raise ValidationError({'department': "Department does not belong to this organization."})

        return cleaned_data
