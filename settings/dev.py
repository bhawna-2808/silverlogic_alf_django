from .base import *  # noqa
from .base import BASE_DIR, URL

DEBUG = True
SECRET_KEY = "1234"

# Email
DEFAULT_FROM_EMAIL = "john@test.com"
DJMAIL_REAL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Must be absolute URLs for use in emails.
MEDIA_ROOT = str(BASE_DIR.parent / "media")
MEDIA_URL = "{url}/media/".format(url=URL)
STATIC_ROOT = str(BASE_DIR.parent / "static")
STATIC_URL = "{url}/static/".format(url=URL)

# Celery
CELERY_ALWAYS_EAGER = True

ENVIRONMENT = "development"
