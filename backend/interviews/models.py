from django.db import models

# Create your models here.

class InterviewSession(models.Model):
    language = models.CharField(max_length=20)
    started_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

class QuestionAnswer(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ClinicalSummary(models.Model):
    session = models.OneToOneField(InterviewSession, on_delete=models.CASCADE)
    soap_note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    pdf = models.FileField(upload_to="reports/", null=True, blank=True)