"""
Django models for Lab Report Analyzer.
"""
import os
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Patient(models.Model):
    """Patient model for storing patient demographics."""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('U', 'Unknown'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ur', 'Urdu (اردو)'),
        ('pa', 'Punjabi (ਪੰਜਾਬੀ)'),
        ('ps', 'Pashto (پښتو)'),
        ('sd', 'Sindhi (سنڌي)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    age = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(150)],
        help_text="Patient age in years"
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='U')
    preferred_language = models.CharField(
        max_length=2, 
        choices=LANGUAGE_CHOICES, 
        default='en',
        help_text="Preferred language for summary and explanations"
    )
    is_pregnant = models.BooleanField(default=False, help_text="Is the patient pregnant? (for reference range adjustment)")
    contact = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
    
    def __str__(self):
        return f"{self.name} (Age: {self.age}, {self.get_gender_display()})"
    
    def get_display_name(self):
        """Return formatted patient name with demographics."""
        pregnancy_info = ", Pregnant" if self.is_pregnant else ""
        return f"{self.name}, {self.age}y, {self.get_gender_display()}{pregnancy_info}"


class LabReport(models.Model):
    """Lab report model for storing uploaded lab reports."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_reports')
    file = models.FileField(upload_to='lab_reports/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Lab Report'
        verbose_name_plural = 'Lab Reports'
        indexes = [
            models.Index(fields=['status', '-uploaded_at']),
            models.Index(fields=['patient', '-uploaded_at']),
        ]
    
    def __str__(self):
        return f"Lab Report {self.id} - {self.patient.name} ({self.status})"
    
    def get_file_extension(self):
        """Get file extension."""
        return os.path.splitext(self.file.name)[1].lower()
    
    def is_pdf(self):
        """Check if file is PDF."""
        return self.get_file_extension() == '.pdf'
    
    def is_image(self):
        """Check if file is an image."""
        return self.get_file_extension() in ['.jpg', '.jpeg', '.png']
    
    def mark_processing(self):
        """Mark report as processing."""
        self.status = 'processing'
        self.save(update_fields=['status'])
    
    def mark_completed(self):
        """Mark report as completed."""
        self.status = 'completed'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
    
    def mark_failed(self, error_message):
        """Mark report as failed with error message."""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])
    
    def delete(self, *args, **kwargs):
        """Override delete to remove file from filesystem."""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)


class AnalysisResult(models.Model):
    """Analysis result model for storing AI-generated analysis."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lab_report = models.OneToOneField(
        LabReport,
        on_delete=models.CASCADE,
        related_name='analysis_result'
    )
    findings = models.JSONField(
        default=dict,
        help_text="Structured JSON containing all analysis findings"
    )
    clinical_summary = models.TextField(blank=True, null=True)
    critical_flags = models.IntegerField(default=0, help_text="Number of critical findings")
    has_critical = models.BooleanField(default=False, db_index=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    processing_time = models.FloatField(blank=True, null=True, help_text="Processing time in seconds")
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'Analysis Result'
        verbose_name_plural = 'Analysis Results'
        indexes = [
            models.Index(fields=['-generated_at']),
            models.Index(fields=['has_critical', '-generated_at']),
        ]
    
    def __str__(self):
        return f"Analysis for {self.lab_report.patient.name} - {self.critical_flags} critical"
    
    def get_critical_findings(self):
        """Get list of critical findings from JSON."""
        return self.findings.get('critical_findings', [])
    
    def get_abnormal_findings(self):
        """Get list of abnormal findings from JSON."""
        return self.findings.get('abnormal_findings', [])
    
    def get_normal_findings(self):
        """Get list of normal findings from JSON."""
        return self.findings.get('normal_findings', [])
    
    def get_soap_note(self):
        """Get SOAP note from clinical summary."""
        return self.findings.get('clinical_summary', {})
    
    def get_metadata(self):
        """Get processing metadata."""
        return self.findings.get('metadata', {})
