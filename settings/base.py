"""
https://docs.djangoproject.com/en/1.9/ref/settings/
"""
import pathlib
import re
from datetime import date, timedelta

from django.utils.translation import gettext_lazy as _

import dj_database_url
import stripe
from celery.schedules import crontab
from kombu import Exchange, Queue
from PIL import Image

from .env import env

BASE_DIR = pathlib.Path(__file__).parent.parent
SETTINGS_DIR = BASE_DIR / "settings"
APPS_DIR = BASE_DIR / "apps"

ALLOWED_HOSTS = ["*"]  # Host checking done by web server.
ROOT_URLCONF = "apps.urls"
WSGI_APPLICATION = "apps.wsgi.application"

# Sites
URL = env("URL")
FRONT_URL = env("FRONT_URL")
FRONT_USER_INVITE_ACCEPT_URL = FRONT_URL + "/user-invite-accept/{id}/{token}"
FRONT_USER_RESIDENT_1823_URL = FRONT_URL + "/residents/{id}/edit-1823"

# Djoser
DOMAIN = re.sub(r"^https?://", "", FRONT_URL).replace("/#", "")

# Mail
EMAIL_BACKEND = "djmail.backends.default.EmailBackend"
DJMAIL_MAX_RETRY_NUMBER = 3

INSTALLED_APPS = [
    # Django
    "django.contrib.admin.apps.SimpleAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    # Third party
    "rest_framework",
    "timed_auth_token",
    "djmail",
    "corsheaders",
    "avatar",
    "easy_thumbnails",
    "django_jinja",
    "crispy_forms",
    "django_filters",
    "django_celery_results",
    "djstripeevents.apps.StripeEventsConfig",
    "djoser",
    "logentry_admin",
    "embed_video",
    "ordered_model",
    "actstream",
    "constance",
    "constance.backends.database",
    # Apps
    "apps.api.apps.ApiConfig",
    "apps.base",
    "apps.examiners",
    "apps.facilities.apps.FacilitiesConfig",
    "apps.trainings.apps.TrainingsConfig",
    "apps.residents.apps.ResidentsConfig",
    "apps.alfdirectory.apps.AlfDirectoryConfig",
    "apps.subscriptions.apps.SubscriptionsConfig",
    "apps.tutorials",
    "apps.activities",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.base.middleware.TimezoneMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django_jinja.backend.Jinja2",
        "DIRS": [str(APPS_DIR / "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "match_extension": ".j2",
            "constants": {
                "URL": URL,
                "FRONT_URL": FRONT_URL,
            },
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(APPS_DIR / "templates")],
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
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases
# https://github.com/kennethreitz/dj-database-url#url-schema
DATABASES = {}
DATABASES["default"] = dj_database_url.parse(env("DATABASE_URL"))

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
DISPLAY_TIME_ZONE = "America/New_York"
USE_I18N = True
USE_L10N = True
USE_TZ = True
LANGUAGES = [
    ("en", _("English")),
]

# For reverse proxying
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTOCOL", "https")

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "formatters": {
        "simple": {"format": "[%(name)s] [%(levelname)s] %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "loggers": {},
}

# Allow requests from any domain.
CORS_ORIGIN_ALLOW_ALL = True

# Rest Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.api.authentication.TimedAuthTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "ORDERING_PARAM": "order_by",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

# Timed Auth Token
TIMED_AUTH_TOKEN = {
    "DEFAULT_VALIDITY_DURATION": timedelta(minutes=int(env("AUTH_TOKEN_DURATION_MINUTES"))),
}

# Avatars
AVATAR_GRAVATAR_DEFAULT = "retro"
AVATAR_STORAGE_DIR = "user-avatars"
AVATAR_CLEANUP_DELETED = True
AVATAR_MAX_AVATARS_PER_USER = 1
AVATAR_AUTO_GENERATE_SIZES = [1024, 64]
AVATAR_RESIZE_METHOD = Image.LANCZOS

# Celery
# http://docs.celeryproject.org/en/latest/configuration.html
exchange_default = Exchange("default")
BROKER_URL = env("CELERY_BROKER_URL")
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_TASK_QUEUES = (
    Queue("default", exchange_default, routing_key="default"),
    Queue("emails", exchange_default, routing_key="emails"),
)
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_DEFAULT_EXCHANGE_TYPE = "direct"
CELERY_TASK_DEFAULT_ROUTING_KEY = "default"
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_BACKEND = "django-db"
CELERY_RESULT_EXTENDED = True
CELERY_ROUTES = {
    "djmail.tasks.send_messages": {"exchange": "default", "routing_key": "emails"},
    "djmail.tasks.retry_send_messages": {"exchange": "default", "routing_key": "emails"},
}
CELERY_BEAT_SCHEDULE = {
    "email-employee-events": {
        "task": "apps.trainings.tasks.email_employee_events",
        "schedule": crontab(minute=0, hour=8),
    },
    "email-scheduled-trainings": {
        "task": "apps.trainings.tasks.email_scheduled_trainings_today",
        "schedule": crontab(minute=0, hour=8),
    },
    "email-overdue-tasks": {
        "task": "apps.trainings.tasks.email_overdue_tasks_this_week",
        "schedule": crontab(minute=0, hour=8),
    },
    "email-facility-compliant": {
        "task": "apps.trainings.tasks.email_facility_compliant",
        "schedule": crontab(minute=0, hour=8),
    },
    "email-completed-trainings-reminder": {
        "task": "apps.trainings.tasks.email_completed_trainings_reminder_today",
        "schedule": crontab(minute=0, hour=8),
    },
    "email-monthly-reminders": {
        "task": "apps.trainings.tasks.email_monthly_reminders",
        "schedule": crontab(minute=0, hour=8, day_of_month=1),
    },
    "reset-prerequisite-tasks": {
        "task": "apps.trainings.tasks.reset_prerequisite_tasks",
        "schedule": crontab(minute=0, hour=8),
    },
    "email-resident-birthday-reminder": {
        "task": "apps.residents.tasks.email_resident_birthday_reminder",
        "schedule": crontab(minute=0, hour=14),
    },
    "email-birthday-reminder": {
        "task": "apps.trainings.tasks.email_birthday_reminder",
        "schedule": crontab(minute=0, hour=14),
    },
    "email-ltc-providers": {
        "task": "apps.residents.tasks.send_ltc_providers_email",
        "schedule": crontab(minute=0, hour=7, day_of_week="monday"),
    },
    "set-resident-is-active": {
        "task": "apps.residents.tasks.set_resident_is_active",
        "schedule": crontab(minute=0, hour=8),
    },
    "set-deactivated-employees": {
        "task": "apps.trainings.tasks.deactivate_employees_after_termination_date",
        "schedule": crontab(minute=0, hour=0),
        "options": {"expires": 60 * 60},
    },
    "import-ahca-facilites": {
        "task": "apps.alfdirectory.tasks.import-ahca-facilities",
        "schedule": crontab(minute=0, hour=8, day_of_month=1, month_of_year="*/3"),
    },
    "mark-staff-subscriptions-as-past-due": {
        "task": "apps.subscriptions.tasks.mark_trials_as_past_due",
        "schedule": crontab(minute=0, hour=6),
    },
    "generate-ils-file": {
        "task": "apps.residents.tasks.generate_ils_file",
        "schedule": crontab(minute=0, hour=4, day_of_month=28),
    },
    "sms-employee-in-person-task": {
        "task": "apps.trainings.tasks.sms_in_person_training_reminders",
        "schedule": timedelta(hours=1),
    },
    "sms-employee-past-due-task": {
        "task": "apps.trainings.tasks.sms_past_due_reminders",
        "schedule": crontab(minute=0, hour=13),
    },
    "sms-employee-upcoming-task": {
        "task": "apps.trainings.tasks.sms_upcoming_reminders",
        "schedule": crontab(minute=0, hour=13),
    },
}

# DJOSER
DJOSER = {
    "DOMAIN": env("DJOSER_DOMAIN"),
    "SITE_NAME": "ALF",
    "PASSWORD_RESET_CONFIRM_URL": "#/password/reset/confirm/{uid}/{token}",
    "ACTIVATION_URL": "#/activate/{uid}/{token}",
    "LOGIN_AFTER_ACTIVATION": True,
    "SEND_ACTIVATION_EMAIL": True,
    "SERIALIZERS": {
        "password_reset": "djoser.serializers.SendEmailResetSerializer",
    },
}

# Stripe
stripe.api_key = env("STRIPE_API_KEY")

# Embed Video
EMBED_VIDEO_BACKENDS = (
    "apps.tutorials.backends.SecureYoutubeBackend",
    "apps.tutorials.backends.SecureWistiaBackend",
)

CUSTOM_TASK_TYPE_ADMIN_EMAIL = env("CUSTOM_TASK_TYPE_ADMIN_EMAIL")

# TWILIO
TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = env("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = env("TWILIO_PHONE_NUMBER")

# SENDGRID
SENDGRID_API_KEY = env("SENDGRID_API_KEY")

# VIRTRU
VIRTRU_HMAC = env("VIRTRU_HMAC_TOKEN")
VIRTRU_SECRET = env("VIRTRU_SECRET")
VIRTRU_OWNER_ADDRESS = "ltcbot@alfboss.com"

# Google API KEY
GOOGLE_API_KEY = env("GOOGLE_API_KEY")

# BRANCH.IO
BRANCHIO_KEY = "key_live_jpNaS4bH2j7fVZTWTYgaNdiiADo61CRU"
BRANCHIO_FALLBACK_URL = "http://alfboss.com/"

# Client IDs
WEB_CLIENT_ID = "1CvcYng7nZYdEh2yG3YMGwYfFcHmag"
APP_CLIENT_ID = "QNfvk1pPPhBD9rIpKEPymUbelbVx9v"
EXTERNAL_CLIENT_ID = "3rpBcCtXdFVN02NPIY2IO1jDbCIWJxwM"

# SFTP
ILS_SFTP_HOST = "sftp.ilshealth.com"
ILS_SFTP_USER = "ALF_BOSS"
ILS_SFTP_PASS = "wrNAG2h"
ILS_SFTP_DEST_FOLDER = ""  # TODO: Add correct folder

# Constance
CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_CONFIG = {
    "ALF_ADMIN_EMAILS": (
        "bw@tsl.io, de@tsl.io, ce@tsl.io, northlake1222@gmail.com, pascal@alfboss.com",
        "Admin emails for ALF",
        str,
    ),
    "SPONSORSHIPS_START": (
        date(2020, 2, 1),
        "Start date to show sponsorship FE opt-in",
        date,
    ),
    "TRAINING_REMINDER_ACTIVE": (False, "Reminder for training", bool),
}

# Misc
DATA_UPLOAD_MAX_MEMORY_SIZE = 1048576 * 100  # 100 MB
