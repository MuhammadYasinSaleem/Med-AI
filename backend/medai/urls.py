"""
URL configuration for medai project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .health import health_check, readiness_check
from .workflow_views import (
    WorkflowSuggestAPIView,
    ExecuteWorkflowAPIView,
    ComprehensiveCareAPIView
)
from .conversation_views import (
    StartConversationAPIView,
    ContinueConversationAPIView,
    GetConversationHistoryAPIView
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Health check endpoints
    path('health/', health_check, name='health'),
    path('ready/', readiness_check, name='readiness'),

    # Unified Orchestrator Workflows
    path('medai/workflow/suggest/', WorkflowSuggestAPIView.as_view(), name='workflow_suggest'),
    path('medai/workflow/execute/', ExecuteWorkflowAPIView.as_view(), name='workflow_execute'),
    path('medai/workflow/comprehensive/', ComprehensiveCareAPIView.as_view(), name='comprehensive_care'),
    
    # Conversational Interface
    path('medai/conversation/start/', StartConversationAPIView.as_view(), name='conversation_start'),
    path('medai/conversation/continue/', ContinueConversationAPIView.as_view(), name='conversation_continue'),
    path('medai/conversation/<str:session_id>/', GetConversationHistoryAPIView.as_view(), name='conversation_history'),

    # Core apps
    path('', include('lab_analyzer.urls')),
    path('medai/interview/', include('interviews.urls')),
    path('medai/medication_interaction/', include('medication_interaction.urls')),
    # path('whatsapp/', include('whatsapp.urls')),  # Commented out - requires twilio
]

# API Documentation (enabled only if drf-spectacular is installed)
if 'drf_spectacular' in settings.INSTALLED_APPS:
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularSwaggerView,
    )

    urlpatterns += [
        path('medai/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('medai/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
    ]

# Serve static & media files ONLY in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
