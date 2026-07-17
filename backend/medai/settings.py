"""
Django settings for medai project.
Production-ready merged configuration.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Base setup
# -------------------------------------------------------------------

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------------------------------------------------------
# Security
# -------------------------------------------------------------------

SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-change-this-in-production'
)

DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Production-ready ALLOWED_HOSTS including your ngrok URL and environment variable support
ALLOWED_HOSTS = os.getenv(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1,uncolorable-martina-expectably.ngrok-free.dev'
).split(',')


# -------------------------------------------------------------------
# Applications
# -------------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'drf_spectacular',
    'corsheaders',  # CORS support for React frontend

    # Local apps
    'lab_analyzer',
    'interviews',
    'medication_interaction',
    'whatsapp',
]


# -------------------------------------------------------------------
# Middleware
# -------------------------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware (should be early)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# -------------------------------------------------------------------
# URLs / WSGI
# -------------------------------------------------------------------

ROOT_URLCONF = 'medai.urls'

WSGI_APPLICATION = 'medai.wsgi.application'


# -------------------------------------------------------------------
# Templates
# -------------------------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# -------------------------------------------------------------------
# Database
# -------------------------------------------------------------------

DB_NAME = os.getenv('DB_NAME')

if DB_NAME:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DB_NAME,
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# -------------------------------------------------------------------
# Password validation
# -------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# -------------------------------------------------------------------
# Internationalization
# -------------------------------------------------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# -------------------------------------------------------------------
# Static & Media files
# -------------------------------------------------------------------

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# -------------------------------------------------------------------
# Upload limits
# -------------------------------------------------------------------

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png']


# -------------------------------------------------------------------
# Default PK
# -------------------------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# -------------------------------------------------------------------
# Django REST Framework
# -------------------------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}


# -------------------------------------------------------------------
# API Documentation (drf-spectacular)
# -------------------------------------------------------------------

SPECTACULAR_SETTINGS = {
    'TITLE': 'MedAI – Clinical Interview Agent API',
    'DESCRIPTION': 'Agentic AI system for multi-step clinical interviews and early risk detection',
    'VERSION': '1.0.0',
}


# -------------------------------------------------------------------
# Celery
# -------------------------------------------------------------------

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE


# -------------------------------------------------------------------
# Gemini / Google API
# -------------------------------------------------------------------

# Universal API Key (paid)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyB8tF9bjsK1hNpzIG74uBOSIQKs77VGx9g')
GOOGLE_API_KEY = GEMINI_API_KEY  # Alias for compatibility


# -------------------------------------------------------------------
# CORS Configuration (for React Frontend)
# -------------------------------------------------------------------

# Get CORS origins from environment variable, with fallback to localhost for development
CORS_ORIGINS_ENV = os.getenv('CORS_ALLOWED_ORIGINS', '')
if CORS_ORIGINS_ENV:
    # Split comma-separated origins from environment variable
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_ENV.split(',')]
else:
    # Default to localhost for development
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:5173',  # Vite default port
        'http://localhost:3000',  # Alternative React port
        'http://localhost:3001',  # Vite fallback port
        'http://127.0.0.1:5173',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:3001',
    ]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_HEADERS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]


# -------------------------------------------------------------------
# Logging (Unicode-safe for Windows)
# -------------------------------------------------------------------

class SafeUnicodeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            super().emit(record)
        except UnicodeEncodeError:
            try:
                msg = self.format(record)
                safe_msg = msg.encode('ascii', 'replace').decode('ascii')
                self.stream.write(safe_msg + self.terminator)
                self.flush()
            except Exception:
                pass


LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': LOG_DIR / 'django.log',
            'encoding': 'utf-8',
            'formatter': 'default',
        },
        'console': {
            '()': SafeUnicodeStreamHandler,
            'formatter': 'default',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'lab_analyzer': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
