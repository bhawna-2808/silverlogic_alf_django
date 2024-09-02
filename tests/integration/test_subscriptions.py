from datetime import timedelta

from django.utils import timezone

import pytest

from apps.subscriptions.models import Subscription

import tests.factories as f

pytestmark = pytest.mark.django_db


class TestSubscription(object):
    def test_is_active_when_status_is_active(self):
        f.SubscriptionFactory(status=Subscription.Status.active)
        assert Subscription.objects.is_active().count() == 1

    def test_is_active_when_status_is_pending_cancel(self):
        f.SubscriptionFactory(status=Subscription.Status.pending_cancel)
        assert Subscription.objects.is_active().count() == 1

    def test_is_active_when_status_is_trialing_and_trial_end_is_in_the_future(self):
        f.SubscriptionFactory(
            status=Subscription.Status.trialing,
            trial_end=timezone.now() + timedelta(days=1),
        )
        assert Subscription.objects.is_active().count() == 1

    def test_is_active_when_status_is_trialing_and_trial_end_is_in_the_past(self):
        f.SubscriptionFactory(
            status=Subscription.Status.trialing,
            trial_end=timezone.now() - timedelta(days=1),
        )
        assert Subscription.objects.is_active().count() == 0

    def test_is_active_when_status_is_anything_else(self):
        f.SubscriptionFactory(status=Subscription.Status.canceled)
        assert Subscription.objects.is_active().count() == 0

    def test_can_create_trial(self):
        Subscription.objects.create_trial(
            facility=f.FacilityFactory(), billing_interval=f.BillingIntervalFactory()
        )

    def test_cancel_trial(self):
        subscription = Subscription.objects.create_trial(
            facility=f.FacilityFactory(), billing_interval=f.BillingIntervalFactory()
        )
        subscription.cancel()
        assert subscription.status == Subscription.Status.canceled
