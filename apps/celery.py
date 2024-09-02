import re

from django.conf import settings

from celery import Celery

app = Celery("apps")
app.config_from_object("django.conf:settings")

# re.sub to remove the `.apps.XConfig` from app entries.
app.autodiscover_tasks(
    lambda: [re.sub(r"\.apps\.\w+Config", "", app) for app in settings.INSTALLED_APPS]
)
