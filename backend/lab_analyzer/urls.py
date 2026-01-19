"""
URL configuration for lab_analyzer app.
"""
from django.urls import path
from . import views

app_name = 'lab_analyzer'

urlpatterns = [
    # HTML Views (for direct browser access)
    path('', views.home, name='home'),
    path('status/<uuid:report_id>/', views.status, name='status'),
    path('results/<uuid:report_id>/', views.results, name='results'),
    path('results/<uuid:report_id>/download/', views.download_summary, name='download_summary'),
    
    # JSON API Endpoints (for React Frontend)
    path('api/upload/', views.api_upload, name='api_upload'),
    path('status/<uuid:report_id>/api/', views.status_api, name='api_status'),
    path('api/results/<uuid:report_id>/', views.api_results, name='api_results'),
]
