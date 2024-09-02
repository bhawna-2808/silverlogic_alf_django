from .base import *  # noqa
from .base import INSTALLED_APPS, LOGGING, env

DEBUG = False
SECRET_KEY = env("SECRET_KEY")

# Email
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
EMAIL_BACKEND = "djmail.backends.celery.EmailBackend"
DJMAIL_REAL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")

# AWS
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")

# Static / Media Files
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
STATICFILES_STORAGE = "s3_folder_storage.s3.StaticStorage"
STATIC_S3_PATH = "static"
STATIC_URL = "https://{}.s3.amazonaws.com/{}/".format(AWS_STORAGE_BUCKET_NAME, STATIC_S3_PATH)
DEFAULT_FILE_STORAGE = "s3_folder_storage.s3.DefaultStorage"
DEFAULT_S3_PATH = "media"
MEDIA_URL = "https://{}.s3.amazonaws.com/{}/".format(AWS_STORAGE_BUCKET_NAME, DEFAULT_S3_PATH)
INSTALLED_APPS += ["storages", "s3_folder_storage"]

# Thumbnails
THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE

# Sentry (raven) error logging
INSTALLED_APPS += ["raven.contrib.django.raven_compat"]
RAVEN_CONFIG = {"dsn": env("SENTRY_DSN")}
LOGGING["handlers"]["sentry"] = {
    "level": "ERROR",
    "class": "raven.contrib.django.handlers.SentryHandler",
}
LOGGING["root"]["handlers"].append("sentry")

# Aweber (create an access token using scripts/create_aweber_access_token.py)
AWEBER_CONSUMER_KEY = env("AWEBER_CONSUMER_KEY")
AWEBER_CONSUMER_SECRET = env("AWEBER_CONSUMER_SECRET")
AWEBER_ACCESS_TOKEN = env("AWEBER_ACCESS_TOKEN")
AWEBER_ACCESS_SECRET = env("AWEBER_ACCESS_SECRET")
AWEBER_TRIAL_LIST_ID = env("AWEBER_TRIAL_LIST_ID")  # Found in list settings on aweber.com

ENVIRONMENT = env("SENTRY_ENVIRONMENT")
