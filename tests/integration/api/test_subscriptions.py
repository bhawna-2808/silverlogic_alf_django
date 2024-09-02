import time
import uuid
from datetime import datetime, timedelta

from django.core import mail
from django.template.loader import render_to_string
from django.utils import timezone

import pytest
import pytz
import stripe
from mock import Mock, patch

from apps.activities.models import Activity
from apps.facilities.models import BusinessAgreement
from apps.subscriptions.models import FacilityPaymentMethod, Plan, Subscription
from apps.trainings.models import Facility

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestSubscriptionCreate(ApiMixin):
    view_name = "subscriptions-list"

    @pytest.fixture
    def mock_data(self):
        with patch("stripe.Customer.create") as mock:
            mock.return_value = Mock(
                id="stripe-customer-id-1",
                subscriptions=Mock(
                    data=[
                        Mock(
                            id="stripe-subscription-id-1",
                            current_period_start=time.time(),
                            current_period_end=time.time(),
                            trial_start=None,
                            trial_end=None,
                        )
                    ]
                ),
            )
            yield {
                "stripe_token": "asdf1231",
                "billing_interval": f.BillingIntervalFactory().pk,
            }

    @pytest.fixture
    def mock_data_trial(self):
        with patch("stripe.Customer.create") as mock:
            mock.return_value = Mock(
                id="stripe-customer-id-1",
                subscriptions=Mock(
                    data=[
                        Mock(
                            id="stripe-subscription-id-1",
                            current_period_start=time.time(),
                            current_period_end=time.time(),
                            trial_start=time.time(),
                            trial_end=time.time(),
                        )
                    ]
                ),
            )
            yield {
                "stripe_token": "asdf1231",
                "billing_interval": f.BillingIntervalFactory().pk,
            }

    @pytest.fixture
    def mock_data_resident(self, mock_data):
        yield {
            "stripe_token": "asdf1231",
            "billing_interval": f.BillingIntervalFactory(plan__module=Plan.Module.resident).pk,
        }

    @pytest.fixture
    def mock_data_staff(self, mock_data):
        yield {
            "stripe_token": "asdf1231",
            "billing_interval": f.BillingIntervalFactory(plan__module=Plan.Module.staff).pk,
        }

    @pytest.fixture
    def mock_data_staff_trial(self, mock_data_trial):
        yield {
            "stripe_token": "asdf1231",
            "billing_interval": f.BillingIntervalFactory(plan__module=Plan.Module.staff).pk,
        }

    @pytest.fixture
    def mock_data_card_error(self):
        with patch("stripe.Customer.create") as mock:
            mock.side_effect = stripe.error.CardError(
                message="bad times guys", param="asd", code="1"
            )
            yield {
                "stripe_token": "asdf1231",
                "billing_interval": f.BillingIntervalFactory().pk,
            }

    @pytest.fixture
    def mock_data_stripe_error(self):
        with patch("stripe.Customer.create") as mock:
            mock.side_effect = stripe.error.StripeError(message="rip my life")
            yield {
                "stripe_token": "asdf1231",
                "billing_interval": f.BillingIntervalFactory().pk,
            }

    @pytest.fixture
    def real_data(self):
        billing_interval = f.BillingIntervalFactory()
        stripe_plan = stripe.Plan.create(
            id=uuid.uuid4(),
            name=billing_interval.plan.name,
            amount=int(billing_interval.amount * 100),
            currency="USD",
            interval=billing_interval.interval,
            interval_count=billing_interval.interval_count,
        )
        billing_interval.stripe_id = stripe_plan.id
        billing_interval.save()

        stripe_token = stripe.Token.create(
            card={
                "number": "4242424242424242",
                "exp_month": 12,
                "exp_year": datetime.now().year + 1,
                "cvc": "123",
            },
        )
        yield {"stripe_token": stripe_token.id, "billing_interval": billing_interval.pk}

        stripe_plan.delete()

    def test_guest_cant_create(self, client, mock_data):
        r = client.post(self.reverse(), mock_data)
        h.responseUnauthorized(r)

    def test_admin_employee_can_create(self, account_admin_client, mock_data):
        r = account_admin_client.post(self.reverse(), mock_data)
        h.responseCreated(r)
        assert Subscription.objects.count() == 1

    def test_subscription_creation_is_tracked(self, account_admin_client, mock_data):
        r = account_admin_client.post(self.reverse(), mock_data)
        h.responseCreated(r)
        assert Activity.objects.count() == 1
        activity = Activity.objects.get()
        subscription = Subscription.objects.get()
        assert activity.actor == account_admin_client.user
        assert activity.verb == "started subscription"
        assert activity.action_object == subscription
        assert activity.target == account_admin_client.facility

    def test_cant_create_resident_subscription_without_signed_business_agreement(
        self, account_admin_client, mock_data_resident
    ):
        BusinessAgreement.objects.all().delete()
        r = account_admin_client.post(self.reverse(), mock_data_resident)
        h.responseBadRequest(r)
        assert (
            r.data["non_field_errors"][0]
            == "You need to sign a business agreement before starting a resident module subscription."
        )

    def test_can_create_staff_subscription_without_signed_business_agreement(
        self, account_admin_client, mock_data_staff
    ):
        BusinessAgreement.objects.all().delete()
        r = account_admin_client.post(self.reverse(), mock_data_staff)
        h.responseCreated(r)

    def test_admin_employee_can_create_for_real(self, account_admin_client, real_data):
        r = account_admin_client.post(self.reverse(), real_data)
        h.responseCreated(r)
        assert Subscription.objects.count() == 1

    def test_stripe_id_gets_set(self, account_admin_client, mock_data):
        r = account_admin_client.post(self.reverse(), mock_data)
        h.responseCreated(r)
        assert Subscription.objects.get().stripe_id == "stripe-subscription-id-1"

    def test_handles_card_errors(self, account_admin_client, mock_data_card_error):
        r = account_admin_client.post(self.reverse(), mock_data_card_error)
        h.responseBadRequest(r)
        assert r.data["stripe_token"] == ["bad times guys"]

    def test_handles_other_stripe_errors(self, account_admin_client, mock_data_stripe_error):
        r = account_admin_client.post(self.reverse(), mock_data_stripe_error)
        h.responseBadRequest(r)
        assert r.data["non_field_errors"] == ["An error has occurred.  Please try again later."]

    def test_cant_create_with_existing_subscription_of_same_module(
        self, account_admin_client, mock_data_resident
    ):
        f.SubscriptionFactory(billing_interval__plan__module=Plan.Module.resident)
        r = account_admin_client.post(self.reverse(), mock_data_resident)
        h.responseBadRequest(r)
        assert r.data["non_field_errors"] == ["You already have a resident module subscription."]

    def test_can_create_with_existing_subscription_of_different_module(
        self, account_admin_client, mock_data_resident
    ):
        f.SubscriptionFactory(billing_interval__plan__module=Plan.Module.staff)
        r = account_admin_client.post(self.reverse(), mock_data_resident)
        h.responseCreated(r)

    def test_can_create_after_trial_has_started(self, account_admin_client, mock_data_staff):
        f.SubscriptionFactory(
            billing_interval__plan__module=Plan.Module.staff,
            status=Subscription.Status.trialing,
            trial_end=timezone.now() + timedelta(days=1),
        )
        r = account_admin_client.post(self.reverse(), mock_data_staff)
        h.responseCreated(r)

    def test_cant_create_one_subscription_on_top_of_another(
        self, account_admin_client, mock_data_staff
    ):
        r = account_admin_client.post(self.reverse(), mock_data_staff)
        h.responseCreated(r)
        r = account_admin_client.post(self.reverse(), mock_data_staff)
        h.responseBadRequest(r)

    def test_saves_trial_dates(self, account_admin_client, mock_data_staff_trial):
        r = account_admin_client.post(self.reverse(), mock_data_staff_trial)
        h.responseCreated(r)

        subscription = Subscription.objects.get()
        assert subscription.trial_start.date() == datetime.now().date()
        assert subscription.trial_end.date() == datetime.now().date()


class TestSubscriptionRetrieve(ApiMixin):
    view_name = "subscriptions-detail"

    def test_guest_cant_retrieve(self, client):
        subscription = f.SubscriptionFactory()
        r = client.get(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseUnauthorized(r)

    def test_admin_employee_cant_retrieve_other_facility_subscription(self, account_admin_client):
        subscription = f.SubscriptionFactory(facility__name="other guy")
        r = account_admin_client.get(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseNotFound(r)

    def test_admin_employee_can_retrieve_own_facility_subscription(self, account_admin_client):
        subscription = f.SubscriptionFactory()
        r = account_admin_client.get(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseOk(r)

    def test_object_keys(self, account_admin_client):
        subscription = f.SubscriptionFactory()
        r = account_admin_client.get(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseOk(r)
        expected = {
            "id",
            "billing_interval",
            "status",
            "current_period_start",
            "current_period_end",
            "trial_start",
            "trial_end",
            "has_stripe_id",
        }
        actual = set(r.data.keys())
        assert expected == actual

    def test_billing_interval_is_expandable(self, account_admin_client):
        subscription = f.SubscriptionFactory()
        r = account_admin_client.get(
            self.reverse(
                kwargs={"pk": subscription.pk},
                query_params={"expand": "billing_interval"},
            )
        )
        h.responseOk(r)
        assert isinstance(r.data["billing_interval"], dict)

    def test_billing_interval_plan_is_expandable(self, account_admin_client):
        subscription = f.SubscriptionFactory()
        r = account_admin_client.get(
            self.reverse(
                kwargs={"pk": subscription.pk},
                query_params={"expand": "billing_interval,billing_interval.plan"},
            )
        )
        h.responseOk(r)
        assert isinstance(r.data["billing_interval"]["plan"], dict)

    def test_has_stripe_id(self, account_admin_client):
        subscription = f.SubscriptionFactory()
        r = account_admin_client.get(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseOk(r)
        assert r.data["has_stripe_id"] is False

        subscription.stripe_id = "some_token"
        subscription.save()
        r = account_admin_client.get(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseOk(r)
        assert r.data["has_stripe_id"] is True


class TestSubscriptionUpdate(ApiMixin):
    view_name = "subscriptions-detail"

    @pytest.fixture
    def mock_stripe_customer_create(self):
        with patch("stripe.Customer.create") as mock:
            mock.return_value = Mock(
                id="stripe-customer-id-1",
                subscriptions=Mock(
                    data=[
                        Mock(
                            id="stripe-subscription-id-1",
                            current_period_start=time.time(),
                            current_period_end=time.time(),
                            trial_start=None,
                            trial_end=None,
                        )
                    ]
                ),
            )
            yield

    @pytest.fixture
    def mock_data_update_billing_interval(self):
        with patch("stripe.Subscription.retrieve") as mock:
            self.subscription_mock = Mock()
            mock.return_value = self.subscription_mock
            yield {"billing_interval": f.BillingIntervalFactory(stripe_id="plan-id-1").pk}

    @pytest.fixture
    def mock_data_update_payment(self):
        with patch("stripe.Subscription.retrieve") as mock:
            self.subscription_mock = Mock()
            mock.return_value = self.subscription_mock
            yield {"stripe_token": "123456"}

    @pytest.fixture
    def mock_data_card_error(self):
        with patch("stripe.Subscription.retrieve") as mock:
            self.subscription_mock = Mock()
            self.save_mock = Mock(
                side_effect=stripe.error.CardError(message="card error :(", param="1", code="1")
            )
            self.subscription_mock.save = self.save_mock
            mock.return_value = self.subscription_mock
            yield {}

    @pytest.fixture
    def mock_data_stripe_error(self):
        with patch("stripe.Subscription.retrieve") as mock:
            self.subscription_mock = Mock()
            self.save_mock = Mock(side_effect=stripe.error.StripeError(message="stripe error :("))
            self.subscription_mock.save = self.save_mock
            mock.return_value = self.subscription_mock
            yield {}

    @pytest.fixture
    def real_data_update_billing_interval(self):
        pass

    @pytest.fixture
    def real_data_update_payment(self):
        pass

    def test_guest_cant_update(self, client):
        subscription = f.SubscriptionFactory()
        r = client.patch(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseUnauthorized(r)

    def test_admin_employee_cant_update_for_other_facility(self, account_admin_client):
        subscription = f.SubscriptionFactory(facility__name="other one")
        r = account_admin_client.patch(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseNotFound(r)

    def test_admin_employee_can_update_for_own_facility(
        self, account_admin_client, mock_data_update_billing_interval
    ):
        subscription = f.SubscriptionFactory(stripe_id="1234")
        r = account_admin_client.patch(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseOk(r)

    def test_cant_update_without_signed_business_agreement(
        self, account_admin_client, mock_data_update_billing_interval
    ):
        subscription = f.SubscriptionFactory(
            stripe_id="1234", billing_interval__plan__module=Plan.Module.resident
        )
        BusinessAgreement.objects.all().delete()
        r = account_admin_client.patch(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseBadRequest(r)
        assert (
            r.data["non_field_errors"][0]
            == "You need to sign a business agreement before updating a resident module subscription."
        )

    def test_can_update_billing_interval(
        self, account_admin_client, mock_data_update_billing_interval
    ):
        subscription = f.SubscriptionFactory(stripe_id="1234")
        r = account_admin_client.patch(
            self.reverse(kwargs={"pk": subscription.pk}),
            mock_data_update_billing_interval,
        )
        h.responseOk(r)
        assert self.subscription_mock.plan == "plan-id-1"

        orig_billing_interval = subscription.billing_interval
        subscription.refresh_from_db()
        new_billing_interval = subscription.billing_interval
        assert orig_billing_interval != new_billing_interval

    def test_can_update_payment(self, account_admin_client, mock_data_update_payment):
        subscription = f.SubscriptionFactory(stripe_id="1234")
        r = account_admin_client.patch(
            self.reverse(kwargs={"pk": subscription.pk}), mock_data_update_payment
        )
        h.responseOk(r)
        assert self.subscription_mock.source == "123456"

    def test_can_update_billing_interval_for_trial(
        self, account_admin_client, mock_data_update_billing_interval
    ):
        subscription = f.SubscriptionFactory(
            status=Subscription.Status.trialing,
            trial_end=datetime(2015, 1, 1, tzinfo=pytz.UTC),
        )
        r = account_admin_client.patch(
            self.reverse(kwargs={"pk": subscription.pk}),
            mock_data_update_billing_interval,
        )
        h.responseOk(r)
        assert self.subscription_mock.plan == "plan-id-1"

        orig_billing_interval = subscription.billing_interval
        subscription.refresh_from_db()
        new_billing_interval = subscription.billing_interval
        assert orig_billing_interval != new_billing_interval

    def test_can_update_payment_for_trial(
        self,
        account_admin_client,
        mock_stripe_customer_create,
        mock_data_update_payment,
    ):
        subscription = f.SubscriptionFactory(
            status=Subscription.Status.trialing,
            trial_end=datetime(2015, 1, 1, tzinfo=pytz.UTC),
        )
        r = account_admin_client.patch(
            self.reverse(kwargs={"pk": subscription.pk}), mock_data_update_payment
        )
        h.responseOk(r)

    def test_handle_card_error(self, account_admin_client, mock_data_card_error):
        subscription = f.SubscriptionFactory(stripe_id="1234")
        r = account_admin_client.patch(
            self.reverse(kwargs={"pk": subscription.pk}), mock_data_card_error
        )
        h.responseBadRequest(r)
        assert self.save_mock.called
        assert r.data["stripe_token"] == ["card error :("]

    def test_handle_other_stripe_error(self, account_admin_client, mock_data_stripe_error):
        subscription = f.SubscriptionFactory(stripe_id="1234")
        r = account_admin_client.patch(
            self.reverse(kwargs={"pk": subscription.pk}), mock_data_stripe_error
        )
        h.responseBadRequest(r)
        assert self.save_mock.called
        assert r.data["non_field_errors"] == ["An error has occurred.  Please try again later."]


class TestSubscriptionDelete(ApiMixin):
    view_name = "subscriptions-detail"

    @pytest.fixture
    def mock_stripe_delete(self):
        with patch("stripe.Subscription.retrieve") as mock:
            self.retrieve_mock = mock
            subscription_mock = Mock()
            self.delete_mock = Mock()
            subscription_mock.delete = self.delete_mock
            self.retrieve_mock.return_value = subscription_mock
            yield

    @pytest.fixture
    def mock_stripe_error(self):
        with patch("stripe.Subscription.retrieve") as mock:
            mock.side_effect = stripe.error.StripeError(message="stripe error :(")
            yield

    @pytest.fixture
    def real_delete(self):
        yield

    def test_guest_cant_delete(self, client):
        subscription = f.SubscriptionFactory()
        r = client.delete(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseUnauthorized(r)

    def test_admin_employee_cant_delete_for_other_facility(self, account_admin_client):
        subscription = f.SubscriptionFactory(facility__name="other")
        r = account_admin_client.delete(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseNotFound(r)

    def test_admin_employee_can_delete_for_own_facility(
        self, account_admin_client, mock_stripe_delete
    ):
        subscription = f.SubscriptionFactory()
        r = account_admin_client.delete(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseNoContent(r)

    def test_subscription_is_not_deleted(self, account_admin_client, mock_stripe_delete):
        subscription = f.SubscriptionFactory()
        r = account_admin_client.delete(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseNoContent(r)
        subscription.refresh_from_db()

    def test_sets_status(self, account_admin_client, mock_stripe_delete):
        subscription = f.SubscriptionFactory()
        r = account_admin_client.delete(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseNoContent(r)
        subscription.refresh_from_db()
        assert subscription.status == Subscription.Status.pending_cancel

    def test_calls_stripe_cancel(self, account_admin_client, mock_stripe_delete):
        subscription = f.SubscriptionFactory(stripe_id="1234")
        r = account_admin_client.delete(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseNoContent(r)
        self.retrieve_mock.assert_called_with("1234")
        self.delete_mock.assert_called_with(at_period_end=True)

    def test_handle_stripe_error(self, account_admin_client, mock_stripe_error):
        subscription = f.SubscriptionFactory(stripe_id="1234")
        r = account_admin_client.delete(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseBadRequest(r)
        assert r.data["non_field_errors"] == [
            "An error occurred while cancelling your subscription, please try again later."
        ]

    def test_cant_delete_when_already_deleted(self, account_admin_client):
        subscription = f.SubscriptionFactory(status=Subscription.Status.pending_cancel)
        r = account_admin_client.delete(self.reverse(kwargs={"pk": subscription.pk}))
        h.responseBadRequest(r)
        assert r.data["non_field_errors"] == ["The subscription has already been deleted."]

    def test_real_delete(self, account_admin_client, real_delete):
        pass


class TestSubscriptionCurrent(ApiMixin):
    view_name = "subscriptions-current"

    def test_guest_cant_get_current(self, client):
        r = client.get(self.reverse())
        h.responseUnauthorized(r)

    def test_admin_employee_can_get_current(self, account_admin_client):
        f.SubscriptionFactory(billing_interval__plan__module=Plan.Module.resident)
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)
        assert r.data["id"]

    def test_admin_employee_can_get_current_when_past_due(self, account_admin_client):
        f.SubscriptionFactory(
            billing_interval__plan__module=Plan.Module.resident,
            status=Subscription.Status.past_due,
        )
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)
        assert r.data["id"]

    def test_when_no_subscription(self, account_admin_client):
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)
        assert r.data == {}


class TestSubscriptionsStartTrial(ApiMixin):
    view_name = "subscriptions-start-trial"

    @pytest.fixture
    def data(self):
        return {
            "stripe_token": "abcde1234",
            "billing_interval": f.BillingIntervalFactory(plan__module=Plan.Module.resident).pk,
        }

    def test_guest_cant_start_trial(self, client):
        r = client.post(self.reverse())
        h.responseUnauthorized(r)

    def test_admin_employee_can_start_trial(self, account_admin_client, data):
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert Subscription.objects.count() == 1

    def test_stripe_token_is_required_for_staff_trial(self, account_admin_client):
        data = {"billing_interval": f.BillingIntervalFactory(plan__module=Plan.Module.staff).pk}
        r = account_admin_client.post(self.reverse(), data)
        h.responseBadRequest(r)
        assert r.data["stripe_token"][0] == "This field is required."
        assert Subscription.objects.count() == 0

    def test_subscription_creation_is_tracked(self, account_admin_client, data):
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert Activity.objects.count() == 1
        activity = Activity.objects.get()
        subscription = Subscription.objects.get()
        assert activity.actor == account_admin_client.user
        assert activity.verb == "started trial subscription"
        assert activity.action_object == subscription
        assert activity.target == account_admin_client.facility

    def test_cant_start_trial_if_facility_already_has_or_had_a_subscription(
        self, account_admin_client, data
    ):
        f.SubscriptionFactory(billing_interval__plan__module=Plan.Module.resident)
        r = account_admin_client.post(self.reverse(), data)
        h.responseBadRequest(r)
        assert r.data["non_field_errors"] == [
            "Your facility is ineligible to start a trial subscription."
        ]

    def test_can_start_trial_if_facility_already_has_or_had_a_subscription_to_non_resident_module(
        self, account_admin_client, data
    ):
        f.SubscriptionFactory(billing_interval__plan__module=Plan.Module.staff)
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)

    def test_can_start_trial_for_staff_module(self, account_admin_client):
        data = {
            "stripe_token": "asdf1231",
            "billing_interval": f.BillingIntervalFactory(plan__module=Plan.Module.staff).pk,
        }
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)

    def test_cant_start_trial_for_staff_module_without_stripe_token(self, account_admin_client):
        data = {"billing_interval": f.BillingIntervalFactory(plan__module=Plan.Module.staff).pk}
        r = account_admin_client.post(self.reverse(), data)
        h.responseBadRequest(r)

    def test_can_start_trial_for_staff_module_without_stripe_token_with_no_payment_flag(
        self, account_admin_client
    ):
        data = {
            "billing_interval": f.BillingIntervalFactory(plan__module=Plan.Module.staff).pk,
            "no_payment": True,
        }
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)

    def test_on_start_trial_creates_or_updates_facility_payment_method(self, account_admin_client):
        data = {
            "stripe_token": "asdf1231",
            "billing_interval": f.BillingIntervalFactory(plan__module=Plan.Module.staff).pk,
        }
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        payment_method = FacilityPaymentMethod.objects.get(facility=account_admin_client.facility)
        assert payment_method.stripe_token == data["stripe_token"]
        assert Subscription.objects.count() == 1
        Subscription.objects.all().delete()

        data = {
            "stripe_token": "changed",
            "billing_interval": f.BillingIntervalFactory(plan__module=Plan.Module.staff).pk,
        }
        r = account_admin_client.post(self.reverse(), data)
        payment_method.refresh_from_db()
        assert payment_method.stripe_token == data["stripe_token"]

    def test_email_not_sent_without_flag(self, account_admin_client, data):
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        facility = Facility.objects.get(id=account_admin_client.facility.id)
        assert len(mail.outbox) == 0
        assert not facility.bought_ebook

    def test_email_not_sent_with_flag_set_to_false(self, account_admin_client, data):
        data["ebook"] = False
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        facility = Facility.objects.get(id=account_admin_client.facility.id)
        assert len(mail.outbox) == 0
        assert not facility.bought_ebook

    def test_email_sent_with_ebook_flag(self, account_admin_client, data, mailoutbox):
        data["ebook"] = True
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        subject = render_to_string("api/emails/ebook-subject.txt", {}).strip()
        facility = Facility.objects.get(id=account_admin_client.facility.id)
        assert len(mailoutbox) == 1
        assert mailoutbox[0].subject == subject
        assert facility.bought_ebook
