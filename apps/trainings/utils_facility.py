from django.utils import timezone

from constance import config


def have_sponsorships_started():
    return config.SPONSORSHIPS_START <= timezone.now().date()
