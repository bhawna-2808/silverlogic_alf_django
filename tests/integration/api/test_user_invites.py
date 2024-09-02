from django.contrib.auth import get_user_model

import pytest
from mock import patch

from apps.examiners.models import Examiner
from apps.facilities.models import FacilityUser, UserInvite, UserInviteResidentAccess
from apps.facilities.tokens import UserInviteTokenGenerator
from apps.trainings.models import Facility

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestUserInviteCreate(ApiMixin):
    view_name = "user-invites-list"

    @pytest.fixture
    def data(self):
        return {
            "email": "bob@example.com",
            "role": UserInvite.Role.manager,
            "can_see_residents": True,
            "can_see_staff": True,
        }

    def test_guest_cant_create(self, client, data):
        r = client.post(self.reverse(), data)
        h.responseUnauthorized(r)

    def test_manager_can_create(self, manager_client, data):
        r = manager_client.post(self.reverse(), data)
        h.responseCreated(r)

    def test_account_admin_can_create(self, account_admin_client, data):
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)

    def test_can_resend(self, account_admin_client, data):
        r = account_admin_client.post(self.reverse(), data)
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)

    def test_cant_create_if_user_with_email_already_exists_in_my_facility(
        self, account_admin_client, data
    ):
        f.FacilityUserFactory(user__username="rick", user__email=data["email"])
        r = account_admin_client.post(self.reverse(), data)
        h.responseBadRequest(r)

    def test_can_invite_if_already_invited_with_different_data(self, account_admin_client, data):
        facility = Facility.objects.get()
        invite = f.UserInviteFactory(
            email=data["email"], facility=facility, can_see_residents=False, can_see_staff=True
        )
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)

        invite.refresh_from_db()
        assert invite.can_see_residents is True

    def test_can_see_residents_is_not_required(self, account_admin_client, data):
        del data["can_see_residents"]
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)

    def test_can_see_staff_is_not_required(self, account_admin_client, data):
        del data["can_see_staff"]
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)

    @patch("apps.sms.send_twilio_sms")
    def test_invite_should_fill_employee_email_and_phone(
        self, send_twilio_sms, account_admin_client
    ):
        send_twilio_sms.return_value = 1
        user = f.UserFactory(username="bob")
        employee = f.EmployeeFactory(user=user, email=None, phone_number=None)
        f.FacilityUserFactory(user=user)

        payload = {
            "email": "bob@example.com",
            "phone_number": "(347) 233-6099",
            "employee": str(employee.id),
            "role": UserInvite.Role.trainings_user,
            "can_see_residents": False,
            "can_see_staff": False,
        }

        r = account_admin_client.post(self.reverse(), payload)
        h.responseCreated(r)

        employee.refresh_from_db()

        assert employee.email == payload["email"]
        assert employee.phone_number == payload["phone_number"]

    @patch("apps.sms.send_twilio_sms")
    def test_invite_should_not_fill_employee_email_and_phone_if_filled_already(
        self, send_twilio_sms, account_admin_client
    ):
        send_twilio_sms.return_value = 1
        user = f.UserFactory(username="bob")
        employee = f.EmployeeFactory(
            user=user, email="actualbob@example.com", phone_number="(346) 233-6099"
        )
        f.FacilityUserFactory(user=user)

        payload = {
            "email": "bob@example.com",
            "phone_number": "(347) 233-6099",
            "employee": str(employee.id),
            "role": UserInvite.Role.trainings_user,
            "can_see_residents": False,
            "can_see_staff": False,
        }

        r = account_admin_client.post(self.reverse(), payload)
        h.responseCreated(r)

        employee.refresh_from_db()

        assert employee.email != payload["email"]
        assert employee.phone_number != payload["phone_number"]


class TestUserInviteEmployeeLink(ApiMixin):
    view_name = "user-invites-employee-link"

    @pytest.fixture
    def data(self):
        user = f.UserFactory()
        employee = f.EmployeeFactory(user=None)
        f.FacilityUserFactory(user=user, role=FacilityUser.Role.trainings_user)

        return {
            "employee": str(employee.id),
            "user": user.id,
        }

    def test_guest_cant_link(self, client, data):
        r = client.post(self.reverse(), data)
        h.responseUnauthorized(r)

    def test_manager_can_link(self, manager_client, data):
        r = manager_client.post(self.reverse(), data)
        h.responseOk(r)

    def test_account_admin_can_link(self, account_admin_client, data):
        r = account_admin_client.post(self.reverse(), data)
        h.responseOk(r)

    def test_should_not_update_users_with_employee(self, account_admin_client, data):
        user = f.UserFactory()
        employee = f.EmployeeFactory(user=user)
        data["employee"] = str(employee.id)
        data["user"] = user.id
        r = account_admin_client.post(self.reverse(), data)
        h.responseBadRequest(r)

    def test_should_update_users_without_employee(self, account_admin_client, data):
        user = f.UserFactory()
        employee = f.EmployeeFactory(user=None)
        f.FacilityUserFactory(user=user, role=FacilityUser.Role.trainings_user)
        data["employee"] = str(employee.id)
        data["user"] = user.id
        r = account_admin_client.post(self.reverse(), data)
        h.responseOk(r)

        employee.refresh_from_db()

        assert employee.user == user


class TestUserInviteRetrieve(ApiMixin):
    view_name = "user-invites-detail"

    def test_guest_cant_retrieve_without_token(self, client):
        invite = f.UserInviteFactory()
        r = client.get(self.reverse(kwargs={"pk": invite.pk}))
        h.responseUnauthorized(r)

    def test_guest_can_retrieve_with_token(self, client):
        invite = f.UserInviteFactory()
        token = UserInviteTokenGenerator().make_token(invite)
        r = client.get(self.reverse(kwargs={"pk": invite.pk}, query_params={"token": token}))
        h.responseOk(r)

    def test_account_admin_can_retrieve(self, account_admin_client):
        invite = f.UserInviteFactory()
        r = account_admin_client.get(self.reverse(kwargs={"pk": invite.pk}))
        h.responseOk(r)

    def test_non_account_admin_cant_retrieve(self, trainings_user_client):
        invite = f.UserInviteFactory(role=UserInvite.Role.trainings_user)
        r = trainings_user_client.get(self.reverse(kwargs={"pk": invite.pk}))
        h.responseForbidden(r)

    def test_account_admin_cant_retrieve_for_other_facility(self, account_admin_client):
        invite = f.UserInviteFactory(facility__name="blarb")
        r = account_admin_client.get(self.reverse(kwargs={"pk": invite.pk}))
        h.responseNotFound(r)

    def test_object_keys(self, account_admin_client):
        invite = f.UserInviteFactory()
        r = account_admin_client.get(self.reverse(kwargs={"pk": invite.pk}))
        h.responseOk(r)
        expected = {
            "id",
            "email",
            "role",
            "status",
            "employee",
            "can_see_residents",
            "can_see_staff",
            "phone_number",
            "employee_detail",
        }
        actual = set(r.data.keys())
        assert expected == actual


class TestUserInviteDelete(ApiMixin):
    view_name = "user-invites-detail"

    def test_guest_cant_delete(self, client):
        invite = f.UserInviteFactory()
        r = client.delete(self.reverse(kwargs={"pk": invite.pk}))
        h.responseUnauthorized(r)

    def test_manager_can_delete(self, manager_client):
        invite = f.UserInviteFactory()
        r = manager_client.delete(self.reverse(kwargs={"pk": invite.pk}))
        h.responseNoContent(r)

    def test_account_admin_cant_delete_for_other_facility(self, account_admin_client):
        invite = f.UserInviteFactory(facility__name="blarb")
        r = account_admin_client.delete(self.reverse(kwargs={"pk": invite.pk}))
        h.responseNotFound(r)

    def test_account_admin_can_delete_for_own_facility(self, account_admin_client):
        invite = f.UserInviteFactory()
        r = account_admin_client.delete(self.reverse(kwargs={"pk": invite.pk}))
        h.responseNoContent(r)


class TestUserInviteList(ApiMixin):
    view_name = "user-invites-list"

    def test_guest_cant_list(self, client):
        r = client.get(self.reverse())
        h.responseUnauthorized(r)

    def test_manager_can_list(self, manager_client):
        r = manager_client.get(self.reverse())
        h.responseOk(r)

    def test_account_admin_can_list(self, account_admin_client):
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)

    def test_list_includes_invite_from_my_facility(self, account_admin_client):
        f.UserInviteFactory()
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 1

    def test_list_excludes_invites_from_other_facilities(self, account_admin_client):
        f.UserInviteFactory(facility__name="blabr")
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 0

    def test_filter_by_status_includes(self, account_admin_client):
        f.UserInviteFactory()
        r = account_admin_client.get(self.reverse(query_params={"status": UserInvite.Status.sent}))
        h.responseOk(r)
        assert len(r.data) == 1

    def test_filter_by_status_excludes(self, account_admin_client):
        f.UserInviteFactory(status=UserInvite.Status.accepted)
        r = account_admin_client.get(self.reverse(query_params={"status": UserInvite.Status.sent}))
        h.responseOk(r)
        assert len(r.data) == 0

    def test_filter_by_resident_includes(self, account_admin_client):
        resident = f.ResidentFactory()
        invite = f.UserInviteFactory()
        f.UserInviteResidentAccessFactory(resident=resident, invite=invite)
        r = account_admin_client.get(self.reverse(query_params={"resident": resident.pk}))
        h.responseOk(r)
        assert len(r.data) == 1

    def test_filter_by_resident_excludes(self, account_admin_client):
        resident = f.ResidentFactory()
        invite = f.UserInviteFactory()
        f.UserInviteResidentAccessFactory(invite=invite)
        r = account_admin_client.get(self.reverse(query_params={"resident": resident.pk}))
        h.responseOk(r)
        assert len(r.data) == 0


class TestUserInviteResidentAccessCreate(ApiMixin):
    view_name = "user-invites-resident-access"

    def test_guest_cant_set(self, client):
        invite = f.UserInviteFactory()
        r = client.post(self.reverse(kwargs={"pk": invite.pk}))
        h.responseUnauthorized(r)

    def test_non_account_admin_cant_set(self, trainings_user_client):
        invite = f.UserInviteFactory()
        r = trainings_user_client.post(self.reverse(kwargs={"pk": invite.pk}))
        h.responseForbidden(r)

    def test_account_admin_cant_set_when_invite_is_not_part_of_their_facility(
        self, account_admin_client
    ):
        invite = f.UserInviteFactory(facility__name="blarg")
        data = {"residents": []}
        r = account_admin_client.post(self.reverse(kwargs={"pk": invite.pk}), data)
        h.responseNotFound(r)

    def test_account_admin_can_set_when_invite_is_part_of_their_facility(
        self, account_admin_client
    ):
        invite = f.UserInviteFactory()
        data = {"residents": []}
        r = account_admin_client.post(self.reverse(kwargs={"pk": invite.pk}), data)
        h.responseOk(r)

    def test_can_add_access(self, account_admin_client):
        invite = f.UserInviteFactory()
        resident = f.ResidentFactory()
        data = {"residents": [resident.pk]}
        r = account_admin_client.post(self.reverse(kwargs={"pk": invite.pk}), data)
        h.responseOk(r)
        assert UserInviteResidentAccess.objects.count() == 1

    def test_can_remove_access(self, account_admin_client):
        invite = f.UserInviteFactory()
        f.UserInviteResidentAccessFactory(invite=invite)
        data = {"residents": []}
        r = account_admin_client.post(self.reverse(kwargs={"pk": invite.pk}), data)
        h.responseOk(r)
        assert UserInviteResidentAccess.objects.count() == 0

    def test_cant_add_access_for_residents_in_other_facilities(self, account_admin_client):
        invite = f.UserInviteFactory()
        resident = f.ResidentFactory(facility__name="blakjsdflw")
        data = {"residents": [resident.pk]}
        r = account_admin_client.post(self.reverse(kwargs={"pk": invite.pk}), data)
        h.responseBadRequest(r)

    def test_cant_change_access_on_accepted_invitation(self, account_admin_client):
        invite = f.UserInviteFactory(status=UserInvite.Status.accepted)
        f.UserInviteResidentAccessFactory(invite=invite)
        data = {"residents": []}
        r = account_admin_client.post(self.reverse(kwargs={"pk": invite.pk}), data)
        h.responseBadRequest(r)
        assert r.data == [
            "This invitation has already been accepted. You can change residents access in Facility Examiners details."
        ]


class TestInviteResidentAccessRetrieve(ApiMixin):
    view_name = "user-invites-resident-access"

    def test_guest_cant_retrieve(self, client):
        invite = f.UserInviteFactory()
        r = client.get(self.reverse(kwargs={"pk": invite.pk}))
        h.responseUnauthorized(r)

    def test_non_account_admin_cant_retrieve(self, trainings_user_client):
        invite = f.UserInviteFactory()
        r = trainings_user_client.get(self.reverse(kwargs={"pk": invite.pk}))
        h.responseForbidden(r)

    def test_account_admin_cant_retrieve_when_invite_is_not_part_of_their_facility(
        self, account_admin_client
    ):
        invite = f.UserInviteFactory(facility__name="blarg")
        r = account_admin_client.get(self.reverse(kwargs={"pk": invite.pk}))
        h.responseNotFound(r)

    def test_account_admin_can_retrieve_when_invite_is_part_of_their_facility(
        self, account_admin_client
    ):
        invite = f.UserInviteFactory()
        r = account_admin_client.get(self.reverse(kwargs={"pk": invite.pk}))
        h.responseOk(r)


class TestUserInviteAccept(ApiMixin):
    view_name = "user-invites-accept"

    @pytest.fixture
    def data(self):
        self.invite = f.UserInviteFactory()
        self.url_kwargs = {"pk": self.invite.pk}
        token = UserInviteTokenGenerator().make_token(self.invite)
        return {
            "token": token,
            "username": "bobby",
            "password": "12345asdfbaas",
            "first_name": "Rick",
            "last_name": "Bob",
            "can_see_residents": True,
            "can_see_staff": True,
        }

    @pytest.fixture
    def examiner_data(self):
        self.invite = f.UserInviteFactory(role=UserInvite.Role.examiner)
        self.url_kwargs = {"pk": self.invite.pk}
        token = UserInviteTokenGenerator().make_token(self.invite)
        return {
            "token": token,
            "username": "bobby",
            "password": "12345asdfbaas",
            "first_name": "Rick",
            "last_name": "Bob",
            "medical_license_number": "12345",
            "can_see_residents": True,
            "can_see_staff": True,
        }

    def test_guest_can_accept(self, client, data):
        r = client.post(self.reverse(), data)
        h.responseOk(r)

    def test_cant_accept_more_than_once(self, client, data):
        r = client.post(self.reverse(), data)
        r = client.post(self.reverse(), data)
        h.responseBadRequest(r)

    def test_when_id_does_not_exist(self, client, data):
        r = client.post(self.reverse(kwargs={"pk": self.invite.pk + 1}), data)
        h.responseBadRequest(r)

    def test_when_token_is_invalid(self, client, data):
        data["token"] = "12345"
        r = client.post(self.reverse(), data)
        h.responseBadRequest(r)

    def test_when_username_already_exists(self, client, data):
        f.UserFactory(username=data["username"])
        r = client.post(self.reverse(), data)
        h.responseBadRequest(r)

    def test_medical_license_number_is_required_for_examiner_invite(self, client, examiner_data):
        examiner_data.pop("medical_license_number")
        r = client.post(self.reverse(), examiner_data)
        h.responseBadRequest(r)
        assert r.data["medical_license_number"] == ["This field is required."]

    def test_examiner_invite_creates_examiner(self, client, examiner_data):
        r = client.post(self.reverse(), examiner_data)
        h.responseOk(r)
        assert (
            Examiner.objects.get().medical_license_number == examiner_data["medical_license_number"]
        )

    def test_update_employee_data(self, client, data):
        UserInvite.objects.all().update(employee=f.EmployeeFactory())

        r = client.post(self.reverse(), data)
        h.responseOk(r)

        employee = UserInvite.objects.get().employee
        assert employee.code_verified

    @pytest.mark.parametrize("can_see_residents", [True, False])
    def test_update_user_permissions_to_see_residents(self, can_see_residents, client, data):
        can_see_residents = False
        UserInvite.objects.update(can_see_residents=can_see_residents)

        data["can_see_residents"] = can_see_residents
        r = client.post(self.reverse(), data)
        h.responseOk(r)

        facility_user = get_user_model().objects.get(username=data["username"]).facility_users
        assert facility_user.can_see_residents == can_see_residents

    @pytest.mark.parametrize("can_see_staff", [True, False])
    def test_update_user_permissions_to_see_staff(self, can_see_staff, client, data):
        can_see_staff = False
        UserInvite.objects.update(can_see_staff=can_see_staff)

        data["can_see_staff"] = can_see_staff
        r = client.post(self.reverse(), data)
        h.responseOk(r)

        facility_user = get_user_model().objects.get(username=data["username"]).facility_users
        assert facility_user.can_see_staff == can_see_staff
