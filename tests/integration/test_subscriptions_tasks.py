from datetime import timedelta

from django.utils import timezone

import pytest

from apps.subscriptions.models import Subscription
from apps.subscriptions.tasks import mark_trials_as_past_due

import tests.factories as f

pytestmark = pytest.mark.django_db


class TestMarkTrialsAsPastDue(object):
    def test_mark_trials_as_past_due(self):
        f.SubscriptionFactory(
            status=Subscription.Status.trialing,
            trial_start=timezone.now() - timedelta(days=32),
            trial_end=timezone.now() - timedelta(days=30),
        )
        mark_trials_as_past_due()
        sub = Subscription.objects.get()
        assert sub.status == Subscription.Status.trial_expired

    def test_do_not_mark_trials_as_past_due(self):
        f.SubscriptionFactory(
            status=Subscription.Status.trialing,
            trial_start=timezone.now() - timedelta(days=32),
            trial_end=timezone.now() + timedelta(days=30),
        )
        mark_trials_as_past_due()
        sub = Subscription.objects.get()
        assert sub.status == Subscription.Status.trialing
