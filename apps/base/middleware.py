from django.conf import settings
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

import pytz


class TimezoneMiddleware(MiddlewareMixin):
    def process_request(self, request):
        timezone.activate(pytz.timezone(settings.DISPLAY_TIME_ZONE))
