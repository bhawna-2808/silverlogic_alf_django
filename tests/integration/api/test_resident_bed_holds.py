from datetime import date, timedelta

from django.utils import timezone

import pytest

from apps.residents.models import ResidentBedHold
from apps.subscriptions.models import Plan, Subscription

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def resident_and_staff_subscription(resident_subscription):
    f.SubscriptionFactory(
        facility=resident_subscription.facility,
        status=Subscription.Status.trialing,
        billing_interval__plan__module=Plan.Module.staff,
        trial_end=timezone.now() - timedelta(days=1),
    )


class TestResidentBedHolds(ApiMixin):
    view_name = "resident-bed-holds-list"

    @pytest.fixture
    def data(self):
        resident = f.ResidentFactory()
        return {
            "resident": resident.id,
            "date_out": "2019-06-21",
        }

    def test_guest_cant_create(self, client):
        r = client.post(self.reverse())
        h.responseUnauthorized(r)

    def test_trainings_user_cant_list(self, trainings_user_client):
        r = trainings_user_client.get(self.reverse())
        h.responseForbidden(r)

    def test_admin_employee_can_create(self, account_admin_client, data):
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert ResidentBedHold.objects.count() == 1

    def test_examiner_can_create(self, examiner_client, data):
        r = examiner_client.post(self.reverse(), data)
        h.responseCreated(r)

    def test_trainings_user_cant_create(self, trainings_user_client, data):
        r = trainings_user_client.post(self.reverse(), data)
        h.responseForbidden(r)

    def test_can_set_date_in(self, account_admin_client, data):
        data["date_in"] = "2019-06-22"
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert ResidentBedHold.objects.get().date_in == date(2019, 6, 22)

    def test_date_in_unique_together_resident(self, account_admin_client, data):
        data["date_in"] = "2019-06-22"
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        r = account_admin_client.post(self.reverse(), data)
        h.responseBadRequest(r)
        assert (
            r.data["non_field_errors"][0] == "The fields resident, date_out must make a unique set."
        )

    def test_cant_set_date_in_before_date_out(self, account_admin_client, data):
        data["date_in"] = "2019-06-20"
        r = account_admin_client.post(self.reverse(), data)
        h.responseBadRequest(r)
        assert r.data["non_field_errors"][0] == "Date in must be after Date out."

    def test_can_set_sent_to(self, account_admin_client, data):
        data["sent_to"] = "a box"
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert ResidentBedHold.objects.get().sent_to == "a box"

    def test_can_set_notes(self, account_admin_client, data):
        data["notes"] = "some notes"
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert ResidentBedHold.objects.get().notes == "some notes"

    def test_can_list_only_current_facility(self, account_admin_client):
        resident = f.ResidentFactory()
        resident2 = f.ResidentFactory(facility=f.FacilityFactory(name="not the same"))
        f.ResidentBedHoldFactory(resident=resident)
        f.ResidentBedHoldFactory(resident=resident2)
        r = account_admin_client.get(self.reverse())
        assert len(r.data) == 1

    def test_can_filter_by_resident(self, account_admin_client):
        resident = f.ResidentFactory()
        resident2 = f.ResidentFactory()
        f.ResidentBedHoldFactory(resident=resident)
        f.ResidentBedHoldFactory(resident=resident2)
        r = account_admin_client.get(self.reverse(query_params={"resident": resident.id}))
        assert len(r.data) == 1


class TestResidentBedHoldsRetrieve(ApiMixin):
    view_name = "resident-bed-holds-detail"

    def test_guest_cant_retrieve(self, client):
        resident_bed_hold = f.ResidentBedHoldFactory()
        r = client.get(self.reverse(kwargs={"pk": resident_bed_hold.pk}))
        h.responseUnauthorized(r)

    def test_trainings_user_cant_retrieve(self, trainings_user_client):
        resident_bed_hold = f.ResidentBedHoldFactory()
        r = trainings_user_client.get(self.reverse(kwargs={"pk": resident_bed_hold.pk}))
        h.responseForbidden(r)

    def test_admin_employee_cant_retrieve_if_resident_is_in_other_facility(
        self, account_admin_client
    ):
        resident_bed_hold = f.ResidentBedHoldFactory(resident__facility__name="blarg")

        r = account_admin_client.get(self.reverse(kwargs={"pk": resident_bed_hold.pk}))
        h.responseNotFound(r)

    def test_admin_employee_can_retrieve_if_resident_is_in_same_facility(
        self, account_admin_client
    ):
        resident_bed_hold = f.ResidentBedHoldFactory()
        r = account_admin_client.get(self.reverse(kwargs={"pk": resident_bed_hold.pk}))
        h.responseOk(r)

    def test_examiner_can_retrieve_if_they_have_been_given_access(self, examiner_client):
        resident = f.ResidentFactory()
        resident_bed_hold = f.ResidentBedHoldFactory(resident=resident)
        f.ResidentAccessFactory(examiner=examiner_client.examiner, resident=resident)
        r = examiner_client.get(self.reverse(kwargs={"pk": resident_bed_hold.pk}))
        h.responseOk(r)

    def test_examiner_cant_retrieve_without_access(
        self, examiner_client, resident_and_staff_subscription
    ):
        resident_bed_hold = f.ResidentBedHoldFactory()
        r = examiner_client.get(self.reverse(kwargs={"pk": resident_bed_hold.pk}))
        h.responseNotFound(r)


class TestResidentBedHoldsUpdate(ApiMixin):
    view_name = "resident-bed-holds-detail"

    @pytest.fixture
    def data(self):
        resident = f.ResidentFactory()
        self.bed_hold = f.ResidentBedHoldFactory(resident=resident)
        return {
            "resident": resident.id,
            "date_out": "2019-06-29",
            "date_in": "2019-06-30",
            "notes": "notes!",
            "sent_to": "sent to!",
        }

    def test_guest_cant_update(self, client, data):
        r = client.patch(self.reverse(kwargs={"pk": self.bed_hold.pk}))
        h.responseUnauthorized(r)

    def test_trainings_user_cant_update(self, trainings_user_client, data):
        r = trainings_user_client.patch(self.reverse(kwargs={"pk": self.bed_hold.pk}))
        h.responseForbidden(r)

    def test_admin_employee_cant_update_if_resident_is_in_other_facility(
        self, account_admin_client, resident_and_staff_subscription
    ):
        bed_hold = f.ResidentBedHoldFactory(resident__facility__name="blarg")
        r = account_admin_client.patch(self.reverse(kwargs={"pk": bed_hold.pk}))
        h.responseNotFound(r)

    def test_can_update_date_out(self, account_admin_client, data):
        data["date_out"] = "2019-06-22"
        r = account_admin_client.patch(self.reverse(kwargs={"pk": self.bed_hold.pk}), data)
        h.responseOk(r)
        self.bed_hold.refresh_from_db()
        assert ResidentBedHold.objects.get().date_out == date(2019, 6, 22)

    def test_can_update_date_in(self, account_admin_client, data):
        data["date_in"] = "2019-07-01"
        r = account_admin_client.patch(self.reverse(kwargs={"pk": self.bed_hold.pk}), data)
        h.responseOk(r)
        self.bed_hold.refresh_from_db()
        assert ResidentBedHold.objects.get().date_in == date(2019, 7, 1)

    def test_cant_update_date_in_before_date_out(self, account_admin_client, data):
        data["date_in"] = "2019-06-20"
        r = account_admin_client.patch(self.reverse(kwargs={"pk": self.bed_hold.pk}), data)
        h.responseBadRequest(r)
        assert r.data["non_field_errors"][0] == "Date in must be after Date out."

    def test_can_update_sent_to(self, account_admin_client, data):
        data["sent_to"] = "a box"
        r = account_admin_client.patch(self.reverse(kwargs={"pk": self.bed_hold.pk}), data)
        h.responseOk(r)
        self.bed_hold.refresh_from_db()
        assert ResidentBedHold.objects.get().sent_to == "a box"

    def test_can_update_notes(self, account_admin_client, data):
        data["notes"] = "some notes"
        r = account_admin_client.patch(self.reverse(kwargs={"pk": self.bed_hold.pk}), data)
        h.responseOk(r)
        self.bed_hold.refresh_from_db()
        assert ResidentBedHold.objects.get().notes == "some notes"


class TestResidentBedHoldsDelete(ApiMixin):
    view_name = "resident-bed-holds-detail"

    def test_guest_cant_delete(self, client):
        resident_bed_hold = f.ResidentBedHoldFactory()
        r = client.delete(self.reverse(kwargs={"pk": resident_bed_hold.pk}))
        h.responseUnauthorized(r)

    def test_trainings_user_cant_delete(self, trainings_user_client):
        resident_bed_hold = f.ResidentBedHoldFactory()
        r = trainings_user_client.delete(self.reverse(kwargs={"pk": resident_bed_hold.pk}))
        h.responseForbidden(r)

    def test_admin_employee_cant_delete_if_resident_is_in_other_facility(
        self, account_admin_client
    ):
        resident_bed_hold = f.ResidentBedHoldFactory(resident__facility__name="blarg")

        r = account_admin_client.delete(self.reverse(kwargs={"pk": resident_bed_hold.pk}))
        h.responseNotFound(r)

    def test_admin_employee_can_delete_if_resident_is_in_same_facility(self, account_admin_client):
        resident_bed_hold = f.ResidentBedHoldFactory()
        r = account_admin_client.delete(self.reverse(kwargs={"pk": resident_bed_hold.pk}))
        h.responseNoContent(r)

    def test_examiner_can_delete_if_they_have_been_given_access(self, examiner_client):
        resident = f.ResidentFactory()
        resident_bed_hold = f.ResidentBedHoldFactory(resident=resident)
        f.ResidentAccessFactory(examiner=examiner_client.examiner, resident=resident)
        r = examiner_client.delete(self.reverse(kwargs={"pk": resident_bed_hold.pk}))
        h.responseNoContent(r)

    def test_examiner_cant_delete_without_access(
        self, examiner_client, resident_and_staff_subscription
    ):
        resident_bed_hold = f.ResidentBedHoldFactory()
        r = examiner_client.delete(self.reverse(kwargs={"pk": resident_bed_hold.pk}))
        h.responseNotFound(r)
