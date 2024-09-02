from decimal import Decimal

from apps.subscriptions.models import BillingInterval

import tests.factories as f


class TestPlan(object):
    def test_str(self):
        assert str(f.PlanFactory.build())

    def test_repr(self):
        assert repr(f.PlanFactory.build())


class TestBillingFrequency(object):
    def test_str_one_month(self):
        billing_frequency = f.BillingIntervalFactory.build(
            amount=Decimal("12.25"),
            interval=BillingInterval.Interval.month,
            interval_count=1,
        )
        assert str(billing_frequency) == "$12.25 every month"

    def test_str_multi_month(self):
        billing_interval = f.BillingIntervalFactory.build(
            amount=Decimal("14.00"),
            interval=BillingInterval.Interval.month,
            interval_count=4,
        )
        assert str(billing_interval) == "$14.00 every 4 months"
