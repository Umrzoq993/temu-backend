from datetime import timedelta
from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-p4kytrsi@ixb5*7*p4dy6a7#+#rg)rkt%vf0&lo*+hw66nd6l@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['.ngrok-free.app', '127.0.0.1', 'localhost']

# CORS Settings - Completely Disable CORS Restrictions
CORS_ALLOW_ALL_ORIGINS = True  # Allows all domains (for development)
CORS_ALLOW_CREDENTIALS = True  # Allow cookies, authentication headers
CORS_ALLOW_METHODS = ["*"]  # Allow all HTTP methods
CORS_ALLOW_HEADERS = ["*"]  # Allow all headers

# Application definition

INSTALLED_APPS = [
    'jazzmin',
    "corsheaders",
    'dal',
    'dal_select2',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'import_export',
    'drf_yasg',
]

JAZZMIN_SETTINGS = {
    "site_title": "My Admin",
    "site_header": "My Project Administration",
    "welcome_sign": "Welcome to My Project Admin",
    "copyright": "My Company",
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"model": "auth.User"},
    ],
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # CORS Middleware (must be placed before CommonMiddleware)
    "csp.middleware.CSPMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
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

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_USER_MODEL = 'accounts.User'

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CSRF Settings
CSRF_TRUSTED_ORIGINS = [
    "https://brightly-immortal-anemone.ngrok-free.app",
]

# Content Security Policy (CSP) Settings
CSP_DEFAULT_SRC = ("'self'",)

# Allow scripts, including blob (Web Workers)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # Allows inline scripts (remove for production)
    "'unsafe-eval'",  # Allows eval() in scripts (remove for production)
    "blob:",  # ✅ Allows Web Workers
    "https://brightly-immortal-anemone.ngrok-free.app",
)

# Allow Web Workers explicitly
CSP_WORKER_SRC = (
    "'self'",
    "blob:",  # ✅ Allows Web Workers
)

# Allow styles (CSS)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://fonts.googleapis.com",
)

# Allow fonts
CSP_FONT_SRC = (
    "'self'",
    "https://fonts.gstatic.com",
)

# Allow images
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https://brightly-immortal-anemone.ngrok-free.app",
)

# Allow connections (APIs, WebSockets)
CSP_CONNECT_SRC = (
    "'self'",
    "https://brightly-immortal-anemone.ngrok-free.app",
)

# Allow object/embed (set to `'none'` if not needed)
CSP_OBJECT_SRC = ("'none'",)

# Upgrade insecure requests (forces HTTPS)
CSP_UPGRADE_INSECURE_REQUESTS = True
