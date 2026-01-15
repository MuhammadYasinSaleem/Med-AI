"""
Health check endpoint for monitoring system status.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
import os


@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint.
    Returns system status and configuration info.
    """
    status = {
        "status": "healthy",
        "version": "1.0.0",
        "services": {}
    }
    
    # Check Gemini API key
    universal_key = 'AIzaSyB8tF9bjsK1hNpzIG74uBOSIQKs77VGx9g'
    gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') or universal_key
    status["services"]["gemini_api"] = {
        "configured": bool(gemini_key),
        "status": "ok" if gemini_key else "missing"
    }
    
    # Check database
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status["services"]["database"] = {
            "status": "ok",
            "type": settings.DATABASES['default']['ENGINE'].split('.')[-1]
        }
    except Exception as e:
        status["services"]["database"] = {
            "status": "error",
            "error": str(e)
        }
        status["status"] = "degraded"
    
    # Check Celery (optional)
    celery_broker = os.getenv('CELERY_BROKER_URL')
    status["services"]["celery"] = {
        "configured": bool(celery_broker),
        "status": "ok" if celery_broker else "not_configured"
    }
    
    # Check file storage
    try:
        media_root = settings.MEDIA_ROOT
        status["services"]["file_storage"] = {
            "status": "ok",
            "path": str(media_root)
        }
    except Exception as e:
        status["services"]["file_storage"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Determine overall status
    if status["status"] != "degraded":
        critical_services = ["gemini_api", "database"]
        for service in critical_services:
            if status["services"][service]["status"] != "ok":
                status["status"] = "unhealthy"
                break
    
    http_status = 200 if status["status"] == "healthy" else 503
    return JsonResponse(status, status=http_status)


@require_http_methods(["GET"])
def readiness_check(request):
    """
    Readiness check endpoint.
    Returns whether the system is ready to accept requests.
    """
    from django.db import connection
    
    checks = {
        "database": False,
        "gemini_api": False
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = True
    except Exception:
        pass
    
    # Check Gemini API key
    universal_key = 'AIzaSyB8tF9bjsK1hNpzIG74uBOSIQKs77VGx9g'
    gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') or universal_key
    checks["gemini_api"] = bool(gemini_key)
    
    ready = all(checks.values())
    
    response = {
        "ready": ready,
        "checks": checks
    }
    
    return JsonResponse(response, status=200 if ready else 503)
