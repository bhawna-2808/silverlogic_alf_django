from django.utils import timezone

import pytest

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestFacilityRetrieve(ApiMixin):
    view_name = "facilities-detail"

    def test_guest_cant_retrieve(self, client):
        facility = f.FacilityFactory()
        r = client.get(self.reverse(kwargs={"pk": facility.pk}))
        h.responseUnauthorized(r)

    def test_user_cant_retrieve_others_facility(self, account_admin_client):
        facility = f.FacilityFactory(name="blob")
        r = account_admin_client.get(self.reverse(kwargs={"pk": facility.pk}))
        h.responseNotFound(r)

    def test_user_can_retrieve_own_facility(self, account_admin_client):
        facility = f.FacilityFactory()
        r = account_admin_client.get(self.reverse(kwargs={"pk": facility.pk}))
        h.responseOk(r)


class TestFacilityUpdate(ApiMixin):
    view_name = "facilities-detail"

    def test_guest_cant_update(self, client):
        facility = f.FacilityFactory()
        r = client.patch(self.reverse(kwargs={"pk": facility.pk}))
        h.responseUnauthorized(r)

    def test_user_cant_update_others_facility(self, account_admin_client):
        facility = f.FacilityFactory(name="blob")
        r = account_admin_client.patch(self.reverse(kwargs={"pk": facility.pk}))
        h.responseNotFound(r)

    def test_non_account_admin_cant_update_own_facility(self, manager_client):
        facility = f.FacilityFactory()
        r = manager_client.patch(self.reverse(kwargs={"pk": facility.pk}))
        h.responseForbidden(r)

    def test_account_admin_can_update_own_facility(self, account_admin_client):
        facility = f.FacilityFactory()
        data = {
            "contact_fax": "(510) 748-8230",
        }
        r = account_admin_client.patch(self.reverse(kwargs={"pk": facility.pk}), data)
        h.responseOk(r)

        facility.refresh_from_db()
        assert facility.contact_fax == data["contact_fax"]

    def test_can_update_questions(self, account_admin_client):
        facility = f.FacilityFactory()
        question = f.FacilityQuestionRuleFactory().facility_question
        data = {"questions": [question.pk]}
        r = account_admin_client.patch(self.reverse(kwargs={"pk": facility.pk}), data)
        h.responseOk(r)
        assert facility.questions.count() == 1

    def test_can_update_admin_signature(self, account_admin_client, image_base64):
        facility = f.FacilityFactory()
        assert not facility.admin_signature
        data = {"admin_signature": image_base64}
        r = account_admin_client.patch(self.reverse(kwargs={"pk": facility.pk}), data)
        h.responseOk(r)
        facility.refresh_from_db()
        assert facility.admin_signature

    def test_email_sent_when_opted_in_sponsorship_date_is_set(self, account_admin_client, outbox):
        facility = f.FacilityFactory()
        assert not facility.opted_in_sponsorship_date
        date = timezone.now().date()
        data = {"opted_in_sponsorship_date": date}
        r = account_admin_client.patch(self.reverse(kwargs={"pk": facility.pk}), data)
        h.responseOk(r)
        facility.refresh_from_db()
        assert facility.opted_in_sponsorship_date == date
        assert len(outbox) == 1

    def test_automatic_trainings_subscription_creation_success(self, account_admin_client):

        # case 1 - with active subscription
        facility = f.FacilityFactory()
        f.SubscriptionFactory(
            status="active",
            facility=facility,
            billing_interval__plan__module="trainings",
            billing_interval__interval="month",
            billing_interval__plan__capacity_limit=14,
        )
        r = account_admin_client.patch(
            self.reverse(kwargs={"pk": facility.pk}),
            {"opted_in_sponsorship_date": timezone.now().date()},
        )
        h.responseOk(r)
        facility.refresh_from_db()

        assert facility.subscriptions.count() == 2

        # case 2 - should not create duplicate subscriptions

        r = account_admin_client.patch(
            self.reverse(kwargs={"pk": facility.pk}),
            {"opted_in_sponsorship_date": timezone.now().date()},
        )
        h.responseOk(r)
        facility.refresh_from_db()

        assert facility.subscriptions.count() == 2

    def test_automatic_trainings_subscription_creation_failure(self, account_admin_client):

        # case 2 - without active subscriptions
        facility = f.FacilityFactory()
        f.SubscriptionFactory(
            status="cancelled",
            facility=facility,
            billing_interval__plan__module="trainings",
            billing_interval__interval="month",
            billing_interval__plan__capacity_limit=14,
        )

        r = account_admin_client.patch(
            self.reverse(kwargs={"pk": facility.pk}),
            {"opted_in_sponsorship_date": timezone.now().date()},
        )
        h.responseOk(r)
        facility.refresh_from_db()

        assert facility.subscriptions.count() == 1
