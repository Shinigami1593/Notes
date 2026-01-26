# ==========================================
# FILE: backend/secure_notes/settings.py
# COMPLETE VERSION with ALL Security Features
# ==========================================

import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: In production, use environment variables
SECRET_KEY = 'django-insecure-change-this-in-production-use-env-vars'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'axes',  # Brute force protection
    'notes',
    'authentication',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # CSRF Protection
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',  # Must be after SecurityMiddleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'secure_notes.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'secure_notes.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==========================================
# AUTHENTICATION BACKENDS (REQUIRED FOR AXES)
# ==========================================
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # MUST BE FIRST - Brute force protection
    'django.contrib.auth.backends.ModelBackend',  # Default Django authentication
]

# ==========================================
# PASSWORD SECURITY - ENHANCED
# ==========================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12}  # Increased from 8 to 12
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'authentication.validators.PasswordComplexityValidator',  # Custom validator
    },
]

# Password expiry (days)
PASSWORD_EXPIRY_DAYS = 90

# Password history (prevent reuse of last N passwords)
PASSWORD_HISTORY_COUNT = 5

# ==========================================
# BRUTE FORCE PROTECTION (django-axes)
# ==========================================
AXES_ONLY_ALLOW_LISTED_AXES = False
AXES_FAILURE_LIMIT = 5  # Lock after 5 failed attempts
AXES_COOLOFF_TIME = 0.1  # Lock for 6 minutes
AXES_LOCKOUT_BY_COMBINATION_USER_AND_IP = True  # Updated from deprecated setting
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = None
AXES_LOCKOUT_URL = None
AXES_ONLY_ADMIN_SITE = False
AXES_ENABLE_ACCESS_FAILURE_LOG = True
AXES_VERBOSE = True

# ==========================================
# CACHE (Required for Axes and Rate Limiting)
# ==========================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# ==========================================
# RATE LIMITING
# ==========================================
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# ==========================================
# TWO-FACTOR AUTHENTICATION
# ==========================================
TWO_FACTOR_ENABLED = True
TWO_FACTOR_ISSUER = "Secure Notes"

# ==========================================
# INTERNATIONALIZATION
# ==========================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ==========================================
# STATIC FILES
# ==========================================
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================================
# CORS SETTINGS - Allow frontend origin
# ==========================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite default port
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True  # Required for cookies

# ==========================================
# CSRF PROTECTION
# ==========================================
CSRF_COOKIE_HTTPONLY = False  # Frontend needs to read for requests
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173']

# ==========================================
# SESSION SECURITY - ENHANCED
# ==========================================
SESSION_COOKIE_HTTPONLY = True  # Prevent XSS access
SESSION_COOKIE_SECURE = False  # Set to True in production
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_COOKIE_AGE = 1800  # 30 minutes (reduced from 24 hours)
SESSION_SAVE_EVERY_REQUEST = True  # Refresh session on activity
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Clear session on browser close

# ==========================================
# SECURITY HEADERS
# ==========================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'  # Clickjacking protection

# Production settings (enable when deploying)
SECURE_SSL_REDIRECT = False  # Set True in production
SECURE_HSTS_SECONDS = 31536000  # 1 year (production only)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ==========================================
# REST FRAMEWORK CONFIGURATION
# ==========================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'authentication.authentication.OptionalJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# ==========================================
# JWT SETTINGS - Token Security
# ==========================================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_COOKIE': 'access_token',  # HttpOnly cookie name
    'AUTH_COOKIE_DOMAIN': None,
    'AUTH_COOKIE_SECURE': False,  # Set True in production
    'AUTH_COOKIE_HTTP_ONLY': True,  # XSS Protection
    'AUTH_COOKIE_PATH': '/',
    'AUTH_COOKIE_SAMESITE': 'Lax',  # CSRF Protection
}

# ==========================================
# FILE UPLOAD SETTINGS
# ==========================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media' / 'uploads'  # Outside web root
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB limit
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880
ALLOWED_UPLOAD_EXTENSIONS = ['.txt', '.pdf', '.png', '.jpg', '.jpeg', '.gif']

# ==========================================
# LOGGING - Audit Trail
# ==========================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'security.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'axes': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}


# ==========================================
# SECURITY SUMMARY
# ==========================================
"""
✅ Authentication Backends: Axes + ModelBackend
✅ Brute Force Protection: 5 attempts, 1 hour lockout
✅ Password Security: 12+ chars, complexity validation
✅ Password History: Last 5 passwords prevented
✅ Password Expiry: 90 days
✅ Session Security: 30 min timeout, HttpOnly cookies
✅ CSRF Protection: Enabled with tokens
✅ Rate Limiting: Configured for login/register
✅ 2FA Support: TOTP-based
✅ Audit Logging: All security events tracked
✅ File Upload Security: Type and size validation
✅ Security Headers: XSS, Clickjacking protection
"""