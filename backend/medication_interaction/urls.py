from django.urls import path
from .views import AnalyzeInteraction

urlpatterns = [
    path('analyze_interaction/', AnalyzeInteraction.as_view(), name='analyze_interaction'),
]