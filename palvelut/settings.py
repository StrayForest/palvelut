from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Temporary bootstrap key only. Production environment validation is a later P0 step.
SECRET_KEY = "p0-bootstrap-only-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

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
        "DIRS": [],
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

# Database wiring is deliberately deferred to the next P0 infrastructure step.
DATABASES = {"default": {"ENGINE": "django.db.backends.dummy"}}

LANGUAGE_CODE = "en"
TIME_ZONE = "Europe/Helsinki"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
