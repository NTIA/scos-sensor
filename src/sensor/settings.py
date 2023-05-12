"""Django settings for scos-sensor project.

Last updated for the following versions:
    Django 3.2.18
    djangorestframework 3.14.0
    drf-spectacular 0.26.2

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/

!!!!!!NOTE!!!!!: This file is replaced when scos-sensor runs in docker. migration_settings.py is used when migrations are
run and runtime_settings is used when scos sensor is run in docker.
Make sure runtime_settings.py and this stay in sync as needed. See entrypoints/api_entrypoints.sh
"""

import os
import sys
from os import path

from cryptography.fernet import Fernet
from django.core.management.utils import get_random_secret_key
from environs import Env

env = Env()

# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# Build paths inside the project like this: path.join(BASE_DIR, ...)
BASE_DIR = path.dirname(path.dirname(path.abspath(__file__)))
REPO_ROOT = path.dirname(BASE_DIR)

FQDN = env("FQDN", "fqdn.unset")

DOCKER_TAG = env("DOCKER_TAG", default=None)
GIT_BRANCH = env("GIT_BRANCH", default=None)
SCOS_SENSOR_GIT_TAG = env("SCOS_SENSOR_GIT_TAG", default="Unknown")

if not DOCKER_TAG or DOCKER_TAG == "latest":
    VERSION_STRING = GIT_BRANCH
else:
    VERSION_STRING = DOCKER_TAG
    if VERSION_STRING.startswith("v"):
        VERSION_STRING = VERSION_STRING[1:]

# Matches api/v1, api/v2, etc...
API_PREFIX_REGEX = r"^api/(?P<version>v[0-9]+)/"

STATIC_ROOT = path.join(BASE_DIR, "static")
STATIC_URL = "/static/"

__cmd = path.split(sys.argv[0])[-1]
IN_DOCKER = env.bool("IN_DOCKER", default=False)
RUNNING_TESTS = "test" in __cmd
RUNNING_DEMO = env.bool("DEMO", default=False)
MOCK_SIGAN = env.bool("MOCK_SIGAN", default=False) or RUNNING_DEMO or RUNNING_TESTS
MOCK_SIGAN_RANDOM = env.bool("MOCK_SIGAN_RANDOM", default=False)


# Healthchecks - the existence of any of these indicates an unhealthy state
SDR_HEALTHCHECK_FILE = path.join(REPO_ROOT, "sdr_unhealthy")
SCHEDULER_HEALTHCHECK_FILE = path.join(REPO_ROOT, "scheduler_dead")

LICENSE_URL = "https://github.com/NTIA/scos-sensor/blob/master/LICENSE.md"

OPENAPI_FILE = path.join(REPO_ROOT, "docs", "openapi.json")

CONFIG_DIR = path.join(REPO_ROOT, "configs")
DRIVERS_DIR = path.join(REPO_ROOT, "drivers")

# JSON configs
if path.exists(path.join(CONFIG_DIR, "sensor_calibration.json")):
    SENSOR_CALIBRATION_FILE = path.join(CONFIG_DIR, "sensor_calibration.json")
if path.exists(path.join(CONFIG_DIR, "sigan_calibration.json")):
    SIGAN_CALIBRATION_FILE = path.join(CONFIG_DIR, "sigan_calibration.json")
if path.exists(path.join(CONFIG_DIR, "sensor_definition.json")):
    SENSOR_DEFINITION_FILE = path.join(CONFIG_DIR, "sensor_definition.json")
MEDIA_ROOT = path.join(REPO_ROOT, "files")
PRESELECTOR_CONFIG = path.join(CONFIG_DIR, "preselector_config.json")

# Cleanup any existing healtcheck files
try:
    os.remove(SDR_HEALTHCHECK_FILE)
except OSError:
    pass

# As defined in SigMF
# TODO: Switch this to Django-native 'iso-8601'
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

# https://docs.djangoproject.com/en/3.2/ref/settings/#internal-ips If
# IN_DOCKER, the IP address that needs to go here to enable the debugging
# toolbar can change each time the bridge network is brought down. It's
# possible to extract the correct address from an incoming request, so if
# IN_DOCKER and DEBUG=true, then the `api_v1_root` view will insert the correct
# IP when the first request comes in.
INTERNAL_IPS = ["127.0.0.1"]

ENCRYPT_DATA_FILES = env.bool("ENCRYPT_DATA_FILES", default=True)

# See /env.template
if not IN_DOCKER or RUNNING_TESTS:
    SECRET_KEY = get_random_secret_key()
    DEBUG = True
    ALLOWED_HOSTS = []
    ENCRYPTION_KEY = Fernet.generate_key()
    ASYNC_CALLBACK = False
else:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECRET_KEY = env.str("SECRET_KEY")
    DEBUG = env.bool("DEBUG", default=False)
    ALLOWED_HOSTS = env.str("DOMAINS").split() + env.str("IPS").split()
    POSTGRES_PASSWORD = env("POSTGRES_PASSWORD")
    ENCRYPTION_KEY = env.str("ENCRYPTION_KEY")
    ASYNC_CALLBACK = env.bool("ASYNC_CALLBACK", default=True)

SESSION_COOKIE_SECURE = IN_DOCKER
CSRF_COOKIE_SECURE = IN_DOCKER
if IN_DOCKER:
    SCOS_TMP = env.str("SCOS_TMP", default="/scos_tmp")
else:
    SCOS_TMP = None

# django-session-timeout https://github.com/LabD/django-session-timeout
SESSION_COOKIE_AGE = 900  # seconds
SESSION_EXPIRE_SECONDS = 900  # seconds
SESSION_EXPIRE_AFTER_LAST_ACTIVITY = True
SESSION_TIMEOUT_REDIRECT = "/api/auth/logout/?next=/api/v1/"

# Application definition

API_TITLE = "SCOS Sensor API"

API_DESCRIPTION = """A RESTful API for controlling a SCOS-compatible sensor.

# Errors

The API uses standard HTTP status codes to indicate the success or failure of
the API call. The body of the response will be JSON in the following format:

## 400 Bad Request (Parse Error)

```json
{
    "field_name": [
        "description of first error",
        "description of second error",
        ...
    ]
}
```

## 400 Bad Request (Protected Error)

```json
{
    "detail": "description of error",
    "protected_objects": [
        "url_to_protected_item_1",
        "url_to_protected_item_2",
        ...
    ]
}
```

## 409 Conflict (DB Integrity Error)

```json
{
    "detail": "description of error"
}
```

"""

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",  # OpenAPI generator
    "drf_spectacular_sidecar",  # required for Django collectstatic discovery
    # project-local apps
    "authentication.apps.AuthenticationConfig",
    "capabilities.apps.CapabilitiesConfig",
    "handlers.apps.HandlersConfig",
    "tasks.apps.TasksConfig",
    "schedule.apps.ScheduleConfig",
    "scheduler.apps.SchedulerConfig",
    "status.apps.StatusConfig",
    "sensor.apps.SensorConfig",  # global settings/utils, etc
    "actions.apps.ActionsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django_session_timeout.middleware.SessionTimeoutMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "sensor.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ],
            "builtins": ["sensor.templatetags.sensor_tags"],
        },
    }
]

WSGI_APPLICATION = "sensor.wsgi.application"

# Django Rest Framework
# http://www.django-rest-framework.org/

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "sensor.exceptions.exception_handler",
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
        "authentication.permissions.RequiredJWTRolePermissionOrIsSuperuser",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",  # this should always point to latest stable api
    "ALLOWED_VERSIONS": ("v1",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 10,
    "DATETIME_FORMAT": DATETIME_FORMAT,
    "DATETIME_INPUT_FORMATS": ("iso-8601",),
    "COERCE_DECIMAL_TO_STRING": False,  # DecimalField should return floats
    "URL_FIELD_NAME": "self",  # RFC 42867
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

AUTHENTICATION = env("AUTHENTICATION", default="")
if AUTHENTICATION == "JWT":
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = (
        "authentication.auth.OAuthJWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    )
else:
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    )

# https://drf-spectacular.readthedocs.io/en/latest/settings.html
SPECTACULAR_SETTINGS = {
    "SCHEMA_PATH_PREFIX": API_PREFIX_REGEX,
    "REDOC_DIST": "SIDECAR",  # Self host Redoc with drf-spectacular-sidecar
    "SERVE_PUBLIC": False,  # Include only endpoints available to user
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAuthenticated"],
    # Schema Metadata
    "TITLE": API_TITLE,
    "DESCRIPTION": API_DESCRIPTION,
    "TOS": None,
    "CONTACT": {"email": "sms@ntia.doc.gov"},
    "LICENSE": {"name": "NTIA/ITS", "url": LICENSE_URL},
    "VERSION": None,  # Render only the request version
    "PREPROCESSING_HOOKS": ["drf_spectacular.hooks.preprocess_exclude_path_format"],
}


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

if RUNNING_TESTS or RUNNING_DEMO:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            # "NAME": ":memory:"
            "NAME": "test.db",  # temporary workaround for https://github.com/pytest-dev/pytest-django/issues/783
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "postgres",
            "USER": "postgres",
            "PASSWORD": env("POSTGRES_PASSWORD"),
            "HOST": "db",
            "PORT": "5432",
        }
    }

if not IN_DOCKER:
    DATABASES["default"]["HOST"] = "localhost"

# Delete oldest TaskResult (and related acquisitions) of current ScheduleEntry if MAX_DISK_USAGE exceeded
MAX_DISK_USAGE = env.int("MAX_DISK_USAGE", default=85)  # percent
# Display at most MAX_TASK_QUEUE upcoming tasks in /tasks/upcoming
MAX_TASK_QUEUE = 50

# Password validation
# https://docs.djangoproject.com/en/3.2/topics/auth/passwords/#password-validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "authentication.User"

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True  # Enable Django's translation system
USE_L10N = True  # Enable localized data formatting
USE_TZ = True  # Make datetimes timezone-aware by default

LOGLEVEL = "DEBUG" if DEBUG else "INFO"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "[%(asctime)s] [%(levelname)s] %(message)s"}},
    "filters": {"require_debug_true": {"()": "django.utils.log.RequireDebugTrue"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "loggers": {
        "actions": {"handlers": ["console"], "level": LOGLEVEL},
        "authentication": {"handlers": ["console"], "level": LOGLEVEL},
        "capabilities": {"handlers": ["console"], "level": LOGLEVEL},
        "handlers": {"handlers": ["console"], "level": LOGLEVEL},
        "schedule": {"handlers": ["console"], "level": LOGLEVEL},
        "scheduler": {"handlers": ["console"], "level": LOGLEVEL},
        "sensor": {"handlers": ["console"], "level": LOGLEVEL},
        "status": {"handlers": ["console"], "level": LOGLEVEL},
        "tasks": {"handlers": ["console"], "level": LOGLEVEL},
        "scos_actions": {"handlers": ["console"], "level": LOGLEVEL},
        "scos_usrp": {"handlers": ["console"], "level": LOGLEVEL},
        "scos_sensor_keysight": {"handlers": ["console"], "level": LOGLEVEL},
        "scos_tekrsa": {"handlers": ["console"], "level": LOGLEVEL},
    },
}


CALLBACK_SSL_VERIFICATION = env.bool("CALLBACK_SSL_VERIFICATION", default=True)
# OAuth Password Flow Authentication
CALLBACK_AUTHENTICATION = env("CALLBACK_AUTHENTICATION", default="")
CALLBACK_TIMEOUT = env.int("CALLBACK_TIMEOUT", default=3)
CLIENT_ID = env("CLIENT_ID", default="")
CLIENT_SECRET = env("CLIENT_SECRET", default="")
USER_NAME = CLIENT_ID
PASSWORD = CLIENT_SECRET

OAUTH_TOKEN_URL = env("OAUTH_TOKEN_URL", default="")
CERTS_DIR = path.join(CONFIG_DIR, "certs")
# Sensor certificate with private key used as client cert
PATH_TO_CLIENT_CERT = env("PATH_TO_CLIENT_CERT", default="")
if PATH_TO_CLIENT_CERT != "":
    PATH_TO_CLIENT_CERT = path.join(CERTS_DIR, PATH_TO_CLIENT_CERT)
# Trusted Certificate Authority certificate to verify authserver and callback URL server certificate
PATH_TO_VERIFY_CERT = env("PATH_TO_VERIFY_CERT", default="")
if PATH_TO_VERIFY_CERT != "":
    PATH_TO_VERIFY_CERT = path.join(CERTS_DIR, PATH_TO_VERIFY_CERT)
# Public key to verify JWT token
PATH_TO_JWT_PUBLIC_KEY = env.str("PATH_TO_JWT_PUBLIC_KEY", default="")
if PATH_TO_JWT_PUBLIC_KEY != "":
    PATH_TO_JWT_PUBLIC_KEY = path.join(CERTS_DIR, PATH_TO_JWT_PUBLIC_KEY)
# Required role from JWT token to access API
REQUIRED_ROLE = "ROLE_MANAGER"

PRESELECTOR_CONFIG = env.str(
    "PRESELECTOR_CONFIG", default=path.join(CONFIG_DIR, "preselector_config.json")
)
PRESELECTOR_MODULE = env.str(
    "PRESELECTOR_MODULE", default="its_preselector.web_relay_preselector"
)
PRESELECTOR_CLASS = env.str("PRESELECTOR_CLASS", default="WebRelayPreselector")
SWITCH_CONFIGS_DIR = env.str(
    "SWITCH_CONFIGS_DIR", default=path.join(CONFIG_DIR, "switches")
)
SIGAN_POWER_CYCLE_STATES = env("SIGAN_POWER_CYCLE_STATES", default=None)
SIGAN_POWER_SWITCH = env("SIGAN_POWER_SWITCH", default=None)
MAX_FAILURES = env("MAX_FAILURES", default=2)

# https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
