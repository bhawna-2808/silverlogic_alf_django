import pytest
from mock import Mock

from apps.api.permissions import (
    FacilityHasResidentSubscription,
    FacilityHasStaffSubscriptionIfRequired,
)
from apps.facilities.models import BusinessAgreement
from apps.subscriptions.models import Plan, Subscription

import tests.factories as f

pytestmark = pytest.mark.django_db


class TestFacilityHasResidentSubscription(object):
    def test_has_subscription(self):
        subscription = f.SubscriptionFactory(billing_interval__plan__module=Plan.Module.resident)
        facility = subscription.facility
        request = Mock(facility=facility)
        permission = FacilityHasResidentSubscription()
        assert permission.has_permission(request, None)

    def test_inactive_subscription(self):
        subscription = f.SubscriptionFactory(
            billing_interval__plan__module=Plan.Module.resident,
            status=Subscription.Status.canceled,
        )
        facility = subscription.facility
        request = Mock(facility=facility)
        permission = FacilityHasResidentSubscription()
        assert not permission.has_permission(request, None)

    def test_no_subscription(self):
        facility = f.FacilityFactory()
        request = Mock(facility=facility)
        permission = FacilityHasResidentSubscription()
        assert not permission.has_permission(request, None)

    def test_has_not_signed_business_agreement(self):
        subscription = f.SubscriptionFactory(billing_interval__plan__module=Plan.Module.resident)
        facility = subscription.facility
        BusinessAgreement.objects.filter(facility=facility).delete()
        request = Mock(facility=facility)
        permission = FacilityHasResidentSubscription()
        assert not permission.has_permission(request, None)

    def test_if_user_has_the_fcc_signup(self):
        subscription = f.SubscriptionFactory(billing_interval__plan__module=Plan.Module.resident)
        facility = subscription.facility
        facility.fcc_signup = True
        facility.save()
        request = Mock(facility=facility)
        permission = FacilityHasResidentSubscription()
        assert permission.has_permission(request, None)


class TestFacilityHasStaffSubscriptionIfRequired(object):
    def test_has_subscription(self):
        subscription = f.SubscriptionFactory(billing_interval__plan__module=Plan.Module.staff)
        facility = subscription.facility
        f.EmployeeFactory.create_batch(16, facility=facility)
        request = Mock(facility=facility)
        permission = FacilityHasStaffSubscriptionIfRequired()
        assert permission.has_permission(request, None)

    def test_inactive_subscription(self):
        subscription = f.SubscriptionFactory(
            billing_interval__plan__module=Plan.Module.staff,
            status=Subscription.Status.canceled,
        )
        facility = subscription.facility
        f.EmployeeFactory.create_batch(16, facility=facility)
        request = Mock(facility=facility)
        permission = FacilityHasStaffSubscriptionIfRequired()
        assert not permission.has_permission(request, None)
        assert permission.message == "staff_subscription_required"

    def test_no_subscription_with_employees(self):
        facility = f.FacilityFactory()
        f.EmployeeFactory.create_batch(16, facility=facility)
        request = Mock(facility=facility)
        permission = FacilityHasStaffSubscriptionIfRequired()
        assert not permission.has_permission(request, None)

    def test_require_trial_subscription_if_none_exists(self):
        facility = f.FacilityFactory()
        request = Mock(facility=facility)
        permission = FacilityHasStaffSubscriptionIfRequired()
        assert not permission.has_permission(request, None)
        assert permission.message == "trial_staff_subscription_required"

    def test_dont_require_trial_subscription_if_fcc_signup(self):
        facility = f.FacilityFactory(fcc_signup=True)
        request = Mock(facility=facility)
        permission = FacilityHasStaffSubscriptionIfRequired()
        assert permission.has_permission(request, None)

    def test_has_not_signed_business_agreement(self):
        subscription = f.SubscriptionFactory(billing_interval__plan__module=Plan.Module.staff)
        facility = subscription.facility
        f.EmployeeFactory.create_batch(16, facility=facility)
        BusinessAgreement.objects.filter(facility=facility).delete()
        request = Mock(facility=facility)
        permission = FacilityHasStaffSubscriptionIfRequired()
        assert permission.has_permission(request, None)
