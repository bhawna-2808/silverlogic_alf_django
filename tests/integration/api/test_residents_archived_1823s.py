from datetime import date, timedelta

from django.conf import settings
from django.utils import timezone

import pytest
from rest_framework.test import APIClient

from apps.facilities.models import FacilityUser, TrainingsTimedAuthToken
from apps.subscriptions.models import Plan, Subscription

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


@pytest.fixture
def resident_and_staff_subscription(resident_subscription):
    f.SubscriptionFactory(
        facility=resident_subscription.facility,
        status=Subscription.Status.trialing,
        billing_interval__plan__module=Plan.Module.staff,
        trial_end=timezone.now() - timedelta(days=1),
    )


class TestArchived1823sList(ApiMixin):
    view_name = "archived-1823s-list"

    def test_admin_can_list(
        self, account_admin_client, resident_and_staff_subscription, image_django_file
    ):
        resident = f.ResidentFactory()
        f.Archived1823Factory(
            resident=resident, data_archived=image_django_file, date_signed=date.today()
        )
        r = account_admin_client.get(self.reverse(kwargs={"parent_pk": resident.pk}))
        h.responseOk(r)
        assert len(r.data) == 1

    def test_guest_cant_list(self, client, resident_and_staff_subscription):
        resident = f.ResidentFactory()
        r = client.get(self.reverse(kwargs={"parent_pk": resident.pk}))
        h.responseUnauthorized(r)


class TestArchived1823sRetrieve(ApiMixin):
    view_name = "archived-1823s-detail"

    def test_token_expires_after_set_time(self, image_django_file, resident_and_staff_subscription):
        employee_client = APIClient()
        facility_user = f.FacilityUserFactory(role=FacilityUser.Role.account_admin)
        f.EmployeeFactory(user=facility_user.user)
        employee_client.facility = facility_user.facility
        resident = f.ResidentFactory()
        archive = f.Archived1823Factory(
            resident=resident, data_archived=image_django_file, date_signed=date.today()
        )

        token = TrainingsTimedAuthToken.objects.create(user=facility_user.user)
        employee_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key} ")
        r = employee_client.get(self.reverse(kwargs={"parent_pk": resident.pk, "pk": archive.pk}))
        h.responseOk(r)

        token.expires = timezone.now() - settings.TIMED_AUTH_TOKEN["DEFAULT_VALIDITY_DURATION"]
        token.save()

        r = employee_client.get(self.reverse(kwargs={"parent_pk": resident.pk, "pk": archive.pk}))

        h.responseUnauthorized(r)

    def test_admin_can_retrieve(
        self, account_admin_client, resident_and_staff_subscription, image_django_file
    ):
        resident = f.ResidentFactory()
        archive = f.Archived1823Factory(
            resident=resident, data_archived=image_django_file, date_signed=date.today()
        )
        r = account_admin_client.get(
            self.reverse(kwargs={"parent_pk": resident.pk, "pk": archive.pk})
        )
        assert r.status_code == 200
        assert r["Content-Type"] == "application/pdf"

    def test_guest_cant_retrieve(self, client, resident_and_staff_subscription, image_django_file):
        resident = f.ResidentFactory()
        archive = f.Archived1823Factory(
            resident=resident, data_archived=image_django_file, date_signed=date.today()
        )
        r = client.get(self.reverse(kwargs={"parent_pk": resident.pk, "pk": archive.pk}))
        h.responseUnauthorized(r)
