"""Django settings for scos-sensor project.

Generated by 'django-admin startproject' using Django 1.11.3.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/

"""

import os
import sys
from os import environ, path

# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# Build paths inside the project like this: path.join(BASE_DIR, ...)
BASE_DIR = path.dirname(path.dirname(path.abspath(__file__)))
REPO_ROOT = path.dirname(BASE_DIR)

DOCKER_TAG = environ.get('DOCKER_TAG')
GIT_BRANCH = environ.get('GIT_BRANCH')
if not DOCKER_TAG or DOCKER_TAG == 'latest':
    VERSION_STRING = GIT_BRANCH
else:
    VERSION_STRING = DOCKER_TAG
    if VERSION_STRING.startswith('v'):
        VERSION_STRING = VERSION_STRING[1:]

STATIC_ROOT = path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    ('js', path.join(STATIC_ROOT, 'js')),
    ('css', path.join(STATIC_ROOT, 'css')),
    ('images', path.join(STATIC_ROOT, 'images')),
    ('fonts', path.join(STATIC_ROOT, 'fonts')),
)

__cmd = path.split(sys.argv[0])[-1]
IN_DOCKER = bool(environ.get('IN_DOCKER'))
RUNNING_TESTS = 'test' in __cmd
RUNNING_DEMO = bool(environ.get('DEMO'))
MOCK_RADIO = bool(environ.get('MOCK_RADIO'))
MOCK_RADIO_RANDOM = bool(environ.get('MOCK_RADIO_RANDOM'))

# Healthchecks - the existance of any of these indicates an unhealthy state
SDR_HEALTHCHECK_FILE = path.join(REPO_ROOT, 'sdr_unhealthy')
SCHEDULER_HEALTHCHECK_FILE = path.join(REPO_ROOT, 'scheduler_dead')

OPENAPI_FILE = path.join(REPO_ROOT, 'docs', 'openapi.json')

SCALE_FACTORS_FILE = path.join(REPO_ROOT, 'scale_factors.json')
SCALE_FACTORS_SCHEMA_FILE = path.join(REPO_ROOT, 'scale_factors_schema.json')

# Cleanup any existing healtcheck files
try:
    os.remove(SDR_HEALTHCHECK_FILE)
except OSError:
    pass

# As defined in SigMF
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

# See /env.template
if not IN_DOCKER or RUNNING_TESTS:
    SECRET_KEY = '!j1&*$wnrkrtc-74cc7_^#n6r3om$6s#!fy=zkd_xp(gkikl+8'
    DEBUG = True
    ALLOWED_HOSTS = []
else:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECRET_KEY = environ['SECRET_KEY']
    DEBUG = environ['DEBUG'] == "true"
    ALLOWED_HOSTS = environ['DOMAINS'].split() + environ['IPS'].split()
    POSTGRES_PASSWORD = environ['POSTGRES_PASSWORD']

SESSION_COOKIE_SECURE = IN_DOCKER
CSRF_COOKIE_SECURE = IN_DOCKER

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
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_openapi',
    'raven.contrib.django.raven_compat',
    # project-local apps
    'acquisitions.apps.AcquisitionsConfig',
    'authentication.apps.AuthenticationConfig',
    'capabilities.apps.CapabilitiesConfig',
    'hardware.apps.HardwareConfig',
    'results.apps.ResultsConfig',
    'schedule.apps.ScheduleConfig',
    'scheduler.apps.SchedulerConfig',
    'status.apps.StatusConfig',
    'sensor.apps.SensorConfig',  # global settings/utils, etc
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sensor.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'builtins': [
                'sensor.templatetags.sensor_tags',
            ]
        },
    },
]

WSGI_APPLICATION = 'sensor.wsgi.application'

# Django Rest Framework
# http://www.django-rest-framework.org/

REST_FRAMEWORK = {
    'EXCEPTION_HANDLER':
    'sensor.exceptions.exception_handler',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES':
    ('rest_framework.permissions.IsAuthenticated', ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_VERSIONING_CLASS':
    'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',  # this should always point to latest stable api
    'ALLOWED_VERSIONS': ('v1', ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
    'DATETIME_FORMAT':
    DATETIME_FORMAT,
    'DATETIME_INPUT_FORMATS': ('iso-8601', ),
    'COERCE_DECIMAL_TO_STRING':
    False,  # DecimalField should return floats
}

# Django Rest Swagger
# http://marcgibbons.github.io/django-rest-swagger/
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'token': {
            'type':
            'apiKey',
            'description':
            ("Tokens are automatically generated for all users. You can "
             "view yours by going to your User Details view in the "
             "browsable API at `/api/v1/users/me` and looking for the "
             "`auth_token` key. Non-admin user accounts do not initially "
             "have a password and so can not log in to the browsable API. "
             "To set a password for a user (for testing purposes), an "
             "admin can do that in the Sensor Configuration Portal, but "
             "only the account's token should be stored and used for "
             "general purpose API access. "
             "Example cURL call: `curl -kLsS -H \"Authorization: Token"
             " 529c30e6e04b3b546f2e073e879b75fdfa147c15\" "
             "https://greyhound5.sms.internal/api/v1`"),
            'name':
            'Token',
            'in':
            'header'
        }
    },
    'APIS_SORTER': 'alpha',
    'OPERATIONS_SORTER': 'method',
    'VALIDATOR_URL': None
}

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

if RUNNING_TESTS or RUNNING_DEMO:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:'
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'postgres',
            'USER': 'postgres',
            'PASSWORD': environ['POSTGRES_PASSWORD'],
            'HOST': 'db',
            'PORT': '5432',
        }
    }

if not IN_DOCKER:
    DATABASES['default']['HOST'] = 'localhost'

# Ensure only the last MAX_TASK_RESULTS results are kept per schedule entry
MAX_TASK_RESULTS = 100

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'authentication.User'

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOGLEVEL = 'DEBUG' if DEBUG else 'INFO'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] [%(levelname)s] %(message)s'
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'actions': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'acquisitions': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'capabilities': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'hardware': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'schedule': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'scheduler': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'sensor': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'status': {
            'handlers': ['console'],
            'level': LOGLEVEL
        }
    }
}

SENTRY_DSN = environ.get('SENTRY_DSN')
if SENTRY_DSN:
    import raven

    RAVEN_CONFIG = {
        'dsn': SENTRY_DSN,
        'release': raven.fetch_git_sha(REPO_ROOT),
    }
