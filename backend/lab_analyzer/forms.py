"""
Django forms for Lab Report Analyzer.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
import os

from .models import Patient, LabReport


class PatientForm(forms.ModelForm):
    """Form for creating/editing Patient."""
    
    class Meta:
        model = Patient
        fields = ['name', 'age', 'gender', 'contact']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter patient name'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Age in years',
                'min': 0,
                'max': 150
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select'
            }),
            'contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact information (optional)'
            }),
        }


class LabReportUploadForm(forms.Form):
    """Form for uploading lab reports."""
    
    patient_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Patient name'
        }),
        label='Patient Name'
    )
    
    age = forms.IntegerField(
        min_value=0,
        max_value=150,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Age in years',
            'min': 0,
            'max': 150
        }),
        label='Age'
    )
    
    gender = forms.ChoiceField(
        choices=Patient.GENDER_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Gender'
    )
    
    preferred_language = forms.ChoiceField(
        choices=Patient.LANGUAGE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Preferred Language',
        help_text='Select language for summary and explanations',
        initial='en'
    )
    
    is_pregnant = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Is Patient Pregnant?',
        help_text='Check if patient is pregnant (for reference range adjustment)'
    )
    
    contact = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contact information (optional)'
        }),
        label='Contact (Optional)'
    )
    
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png',
            'id': 'file-input'
        }),
        label='Lab Report File',
        help_text='Upload PDF, JPG, JPEG, or PNG file (max 10MB)'
    )
    
    def clean_file(self):
        """Validate uploaded file."""
        file = self.cleaned_data.get('file')
        
        if not file:
            raise ValidationError('Please select a file to upload.')
        
        # Check file size (10MB limit)
        if file.size > 10 * 1024 * 1024:
            raise ValidationError('File size exceeds 10MB limit.')
        
        # Check file extension
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f'Invalid file type. Allowed types: {", ".join(settings.ALLOWED_EXTENSIONS)}'
            )
        
        # Sanitize filename
        file.name = self._sanitize_filename(file.name)
        
        return file
    
    def _sanitize_filename(self, filename):
        """Sanitize filename to prevent security issues."""
        import re
        # Remove path components
        filename = os.path.basename(filename)
        # Remove special characters except dots, dashes, and underscores
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        return filename
    
    def save(self):
        """Save patient and lab report."""
        # Create or get patient
        patient, created = Patient.objects.get_or_create(
            name=self.cleaned_data['patient_name'],
            age=self.cleaned_data['age'],
            gender=self.cleaned_data['gender'],
            defaults={
                'contact': self.cleaned_data.get('contact', ''),
                'is_pregnant': self.cleaned_data.get('is_pregnant', False),
                'preferred_language': self.cleaned_data.get('preferred_language', 'en')
            }
        )
        # Update pregnancy status and language if patient already exists
        if not created:
            patient.is_pregnant = self.cleaned_data.get('is_pregnant', False)
            patient.preferred_language = self.cleaned_data.get('preferred_language', 'en')
            patient.save()
        
        # Create lab report
        lab_report = LabReport.objects.create(
            patient=patient,
            file=self.cleaned_data['file'],
            original_filename=self.cleaned_data['file'].name
        )
        
        return lab_report
