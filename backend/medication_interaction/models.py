# Create your models here.
from django.db import models

class MedicationSession(models.Model):
    # Tracking the patient context
    language = models.CharField(max_length=20, default="english")
    patient_age = models.IntegerField(null=True, blank=True)
    conditions = models.TextField(help_text="e.g., CKD Stage 3, Diabetes")
    created_at = models.DateTimeField(auto_now_add=True)

class PatientMedication(models.Model):
    session = models.ForeignKey(MedicationSession, on_delete=models.CASCADE, related_name="medications")
    med_name = models.CharField(max_length=255)
    is_new = models.BooleanField(default=False, help_text="Is this the drug they want to start?") 

class InteractionReport(models.Model):
    session = models.OneToOneField(MedicationSession, on_delete=models.CASCADE)
    severity = models.CharField(max_length=50) # CONTRAINDICATED / MAJOR / MODERATE / MINOR 
    raw_analysis = models.TextField()
    soap_note = models.TextField()