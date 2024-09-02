import logging

from django.utils import timezone

from celery import shared_task

from .models import Subscription

logger = logging.getLogger(__name__)


@shared_task
def mark_trials_as_past_due():
    Subscription.objects.filter(
        status=Subscription.Status.trialing, trial_end__lte=timezone.now()
    ).exclude(current_period_end__gt=timezone.now()).update(
        status=Subscription.Status.trial_expired
    )
