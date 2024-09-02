from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User

import pytest
from freezegun import freeze_time

from apps.activities.models import Activity
from apps.facilities.models import FacilityUser
from apps.subscriptions.models import Plan

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestLogin(ApiMixin):
    view_name = "login-list"

    @pytest.fixture
    def data(self):
        return {
            "username": "admin",
            "password": "admin",
            "client_id": settings.WEB_CLIENT_ID,
        }

    def test_user_can_login_with_facility_link(self, client, data):
        f.FacilityUserFactory(user__username="admin")
        r = client.post(self.reverse(), data=data)
        h.responseOk(r)

    def test_user_login_is_tracked(self, client, data):
        f.FacilityUserFactory(user__username="admin")
        r = client.post(self.reverse(), data=data)
        h.responseOk(r)
        assert Activity.objects.count() == 1
        activity = Activity.objects.get()
        user = User.objects.get(username="admin")
        assert activity.actor == user
        assert activity.verb == "logged in"
        assert activity.action_object == user

    def test_user_cant_login_facility_link(self, client, data):
        f.UserFactory()
        r = client.post(self.reverse(), data=data)
        h.responseBadRequest(r)

    def test_cant_login_with_wrong_password(self, client, data):
        f.FacilityUserFactory(user__username="admin")
        data["password"] = "notpassword"
        r = client.post(self.reverse(), data=data)
        h.responseBadRequest(r)
        assert r.data["password"][0] == "Incorrect password."

    def test_can_login_to_app_client_if_trainings_user(self, client, data):
        user = f.FacilityUserFactory(user__username="admin", role=FacilityUser.Role.trainings_user)
        f.SubscriptionFactory(
            facility=user.facility, billing_interval__plan__module=Plan.Module.trainings
        )
        data["client_id"] = settings.APP_CLIENT_ID
        r = client.post(self.reverse(), data=data)
        h.responseOk(r)

    def test_client_id_is_required(self, client, data):
        f.FacilityUserFactory(user__username="admin", role=FacilityUser.Role.trainings_user)
        del data["client_id"]
        r = client.post(self.reverse(), data=data)
        h.responseBadRequest(r)
        assert r.data["client_id"][0] == "This field is required."

    def test_client_id_is_cant_be_random_stuff(self, client, data):
        f.FacilityUserFactory(user__username="admin", role=FacilityUser.Role.trainings_user)
        data["client_id"] = "heylookatmyrandomclientid"
        r = client.post(self.reverse(), data=data)
        h.responseBadRequest(r)
        assert r.data["client_id"][0] == "Please provide a valid client id"

    def test_cant_login_to_app_if_no_subscription(self, client, data):
        with freeze_time(datetime(2020, 1, 31)):
            # Different date because of SPONSORSHIPS_START
            f.FacilityUserFactory(user__username="admin", role=FacilityUser.Role.trainings_user)
            data["client_id"] = settings.APP_CLIENT_ID
            r = client.post(self.reverse(), data=data)
            h.responseBadRequest(r)

    def test_deactivated_employee_cant_login(self, client, data):
        user = f.FacilityUserFactory(user__username="admin", role=FacilityUser.Role.trainings_user)
        f.SubscriptionFactory(
            facility=user.facility, billing_interval__plan__module=Plan.Module.trainings
        )
        f.EmployeeFactory(user=user.user, is_active=False)
        data["client_id"] = settings.APP_CLIENT_ID
        r = client.post(self.reverse(), data=data)
        h.responseBadRequest(r)
        assert (
            r.data["non_field_errors"][0]
            == "You are no longer associated with this Facility. Please contact your Facility Administrator"
        )

    def test_active_employee_can_login(self, client, data):
        user = f.FacilityUserFactory(user__username="admin", role=FacilityUser.Role.trainings_user)
        f.SubscriptionFactory(
            facility=user.facility, billing_interval__plan__module=Plan.Module.trainings
        )
        f.EmployeeFactory(user=user.user, is_active=True)
        data["client_id"] = settings.APP_CLIENT_ID
        r = client.post(self.reverse(), data=data)
        h.responseOk(r)


class TestInviteCodeVerify(ApiMixin):
    view_name = "login-verify"

    def test_user_can_verify_invite_code(self, client):
        employee = f.EmployeeFactory(invite_code="AAAAAA")
        r = client.post(self.reverse(), data={"code": "AAAAAA"})
        h.responseOk(r)
        assert r.data["id"] == employee.id
        assert r.data["first_name"] == employee.first_name
        assert r.data["last_name"] == employee.last_name
        assert r.data["phone_number"] == employee.phone_number

    def test_user_cant_verify_wrong_invite_code(self, client):
        f.EmployeeFactory(invite_code="AAAAAA")
        r = client.post(self.reverse(), data={"code": "WRONG"})
        h.responseBadRequest(r)
