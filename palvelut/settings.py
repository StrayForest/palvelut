import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Temporary bootstrap key only. Production environment validation is a later P0 step.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "p0-bootstrap-only-not-for-production")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [host for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",") if host]

DOMAIN_APPS = [
    "palvelut.apps.accounts.apps.AccountsConfig",
    "palvelut.apps.taxonomy.apps.TaxonomyConfig",
    "palvelut.apps.providers.apps.ProvidersConfig",
    "palvelut.apps.publishing.apps.PublishingConfig",
    "palvelut.apps.verification.apps.VerificationConfig",
    "palvelut.apps.moderation.apps.ModerationConfig",
    "palvelut.apps.discovery.apps.DiscoveryConfig",
    "palvelut.apps.analytics.apps.AnalyticsConfig",
    "palvelut.apps.content.apps.ContentConfig",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    *DOMAIN_APPS,
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "palvelut.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "palvelut.wsgi.application"
ASGI_APPLICATION = "palvelut.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "palvelut"),
        "USER": os.getenv("POSTGRES_USER", "palvelut"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "palvelut-local-only"),
        "HOST": os.getenv("POSTGRES_HOST", "postgres"),
        "PORT": int(os.getenv("POSTGRES_PORT", "5432")),
    }
}

VALKEY_URL = os.getenv("VALKEY_URL", "redis://valkey:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": VALKEY_URL,
    }
}

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://valkey:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://valkey:6379/2")
CELERY_TIMEZONE = "Europe/Helsinki"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "mailpit")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "1025"))
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "palvelut@local.invalid")

OBJECT_STORAGE_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")
OBJECT_STORAGE_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID", "palvelut-local")
OBJECT_STORAGE_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY", "palvelut-local-only")
OBJECT_STORAGE_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "palvelut-local")

LANGUAGE_CODE = "en"
LANGUAGES = [
    ("ru", "Russian"),
    ("fi", "Finnish"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Europe/Helsinki"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/palvelut/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
