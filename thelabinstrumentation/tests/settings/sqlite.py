from threading import Thread
import os
import random

from fakeredis import TcpFakeServer

# Start a fakeredis server thread
redis_addr = ("127.0.0.1", random.randrange(20_000, 30_000))
server = TcpFakeServer(redis_addr, server_type="redis")
t = Thread(target=server.serve_forever, daemon=True)
t.start()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "test-secret-key-not-for-production"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_rq",
    "thelabinstrumentation",
    "thelabinstrumentation.rq",
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

ROOT_URLCONF = "thelabinstrumentation.tests.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Redis configuration for django-rq (using fakeredis for tests)
RQ_QUEUES = {
    "default": {
        "HOST": redis_addr[0],
        "PORT": redis_addr[1],
        "DB": 0,
        "DEFAULT_TIMEOUT": 360,
    },
    "high": {
        "HOST": redis_addr[0],
        "PORT": redis_addr[1],
        "DB": 0,
    },
    "low": {
        "HOST": redis_addr[0],
        "PORT": redis_addr[1],
        "DB": 0,
    },
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "thelabinstrumentation": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

# TheLab Instrumentation configuration
THELAB_INSTRUMENTATION = {
    "UPDATE_INTERVAL": 5,  # Shorter interval for tests
    "BACKEND": "thelabinstrumentation.backends.logging.LoggingBackend",
    # "OPTIONS": {},
    "DIMENSIONS": {
        "Environment": "test",
        "Application": "thelab-instrumentation-tests",
        "Team": "backend",
    },
}
