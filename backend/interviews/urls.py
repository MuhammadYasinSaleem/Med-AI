from django.urls import path
from .views import StartInterview, SubmitAnswer, GenerateSummary, TriageAPIView, DownloadPDF

urlpatterns = [
    path('start/', StartInterview.as_view()),
    path('answer/', SubmitAnswer.as_view()),
    path('summary/', GenerateSummary.as_view()),
    path('triage/', TriageAPIView.as_view()),
    path('pdf/<int:session_id>/', DownloadPDF.as_view(), name='download_pdf'),
]