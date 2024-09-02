import pytest

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestPlanRetrieve(ApiMixin):
    view_name = "plans-detail"

    def test_guest_can_retrieve(self, client):
        plan = f.PlanFactory()
        r = client.get(self.reverse(kwargs={"pk": plan.pk}))
        h.responseOk(r)

    def test_object_keys(self, client):
        plan = f.PlanFactory()
        r = client.get(self.reverse(kwargs={"pk": plan.pk}))
        h.responseOk(r)
        expected = {"id", "name", "module", "capacity_limit", "billing_intervals"}
        actual = set(r.data.keys())
        assert expected == actual

    def test_billing_intervals_object_keys(self, client):
        plan = f.PlanFactory()
        f.BillingIntervalFactory(plan=plan)
        r = client.get(self.reverse(kwargs={"pk": plan.pk}))
        h.responseOk(r)
        expected = {"id", "amount", "interval", "interval_count"}
        actual = set(r.data["billing_intervals"][0].keys())
        assert expected == actual


class TestPlanList(ApiMixin):
    view_name = "plans-list"

    def test_guest_can_list(self, client):
        f.PlanFactory()
        r = client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 1
