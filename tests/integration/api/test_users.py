import pytest

from apps.api.facilities.serializers import UserResidentAccessSerializer
from apps.facilities.models import FacilityUser, UserResidentAccess

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestUsersDelete(ApiMixin):
    view_name = "users-detail"

    def test_guest_cant_delete(self, client):
        user = f.FacilityUserFactory().user
        r = client.delete(self.reverse(kwargs={"pk": user.pk}))
        h.responseUnauthorized(r)

    def test_manager_cant_delete(self, manager_client):
        user = f.FacilityUserFactory(user__username="bob").user
        r = manager_client.delete(self.reverse(kwargs={"pk": user.pk}))
        h.responseForbidden(r)

    def test_account_admin_can_delete(self, account_admin_client):
        user = f.FacilityUserFactory(user__username="bob").user
        r = account_admin_client.delete(self.reverse(kwargs={"pk": user.pk}))
        h.responseNoContent(r)

    def test_account_admin_cant_delete_themselves(self, account_admin_client):
        r = account_admin_client.delete(self.reverse(kwargs={"pk": account_admin_client.user.pk}))
        h.responseBadRequest(r)


class TestUsersList(ApiMixin):
    view_name = "users-list"

    def test_guest_cant_list(self, client):
        r = client.get(self.reverse())
        h.responseUnauthorized(r)

    def test_manager_cant_list(self, manager_client):
        r = manager_client.get(self.reverse())
        h.responseForbidden(r)

    def test_account_admin_can_list(self, account_admin_client):
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)

    def test_list_includes_users_in_my_facility(self, account_admin_client):
        f.FacilityUserFactory(user__username="rick")
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)
        assert "rick" in [user["username"] for user in r.data]

    def test_list_excludes_users_in_other_facilities(self, account_admin_client):
        f.FacilityUserFactory(user__username="bob", facility__name="tims")
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)
        assert "bob" not in [user["username"] for user in r.data]

    def test_list_excludes_users_in_no_facility(self, account_admin_client):
        f.UserFactory(username="peter")
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)
        assert "peter" not in [user["username"] for user in r.data]

    def test_list_includes_user_employee(self, account_admin_client):
        user = f.UserFactory(username="peter")
        employee = f.EmployeeFactory(user=user)
        f.FacilityUserFactory(user=user)

        r = account_admin_client.get(self.reverse())
        h.responseOk(r)

        for user in r.data:
            if getattr(user, "facility_user", None):
                assert employee.id == user["facility_user"]["employee"]["id"]

    def test_can_filter_users_by_linked(self, account_admin_client):
        f.FacilityUserFactory(user__username="john")
        user = f.UserFactory(username="peter")
        f.EmployeeFactory(user=user)
        f.FacilityUserFactory(user=user)

        r = account_admin_client.get(self.reverse(query_params={"not_linked": True}))
        h.responseOk(r)

        assert "peter" not in [user["username"] for user in r.data]
        assert "john" in [user["username"] for user in r.data]

        r = account_admin_client.get(self.reverse(query_params={"not_linked": False}))
        h.responseOk(r)

        assert "peter" in [user["username"] for user in r.data]
        assert "john" not in [user["username"] for user in r.data]


class TestUsersRetrieve(ApiMixin):
    view_name = "users-detail"

    def test_guest_cant_get(self, client):
        user = f.UserFactory()
        r = client.get(self.reverse(kwargs={"pk": user.pk}))
        h.responseUnauthorized(r)

    def test_manager_cant_get(self, manager_client):
        user = f.UserFactory()
        r = manager_client.get(self.reverse(kwargs={"pk": user.pk}))
        h.responseForbidden(r)

    def test_account_admin_can_get(self, account_admin_client):
        user = f.UserFactory()
        f.FacilityUserFactory(user=user)
        r = account_admin_client.get(self.reverse(kwargs={"pk": user.pk}))
        h.responseOk(r)

    def test_list_manager_resident_access(self, account_admin_client):
        user = f.UserFactory()
        facility_user = f.FacilityUserFactory(user=user, role=FacilityUser.Role.manager)

        resident_access_list = [
            f.UserResidentAccessFactory(user=facility_user),
            f.UserResidentAccessFactory(user=facility_user),
        ]

        r = account_admin_client.get(self.reverse(kwargs={"pk": user.pk}))
        h.responseOk(r)

        resident_access_response = r.data["resident_access"]
        assert len(resident_access_response) == len(resident_access_list)

        for resident_access in resident_access_list:
            resident_access_data = UserResidentAccessSerializer(resident_access).data
            assert resident_access_data in resident_access_response


class TestUsersUpdate(ApiMixin):
    view_name = "users-detail"

    def test_guest_cant_update(self, client):
        user = f.UserFactory()
        r = client.patch(self.reverse(kwargs={"pk": user.pk}))
        h.responseUnauthorized(r)

    def test_manager_cant_update(self, manager_client):
        user = f.UserFactory()
        r = manager_client.patch(self.reverse(kwargs={"pk": user.pk}))
        h.responseForbidden(r)

    def test_account_admin_can_update(self, account_admin_client):
        user = f.UserFactory()
        f.FacilityUserFactory(user=user)
        r = account_admin_client.patch(self.reverse(kwargs={"pk": user.pk}))
        h.responseOk(r)

    def test_update_manager_resident_access(self, account_admin_client):
        user = f.UserFactory()
        facility_user = f.FacilityUserFactory(user=user, role=FacilityUser.Role.manager)
        facility = facility_user.facility

        resident1 = f.ResidentFactory(facility=facility)  # Update ResidentAccess
        resident2 = f.ResidentFactory(facility=facility)  # Create ResidentAccess

        # user_resident_access to update
        f.UserResidentAccessFactory(user=facility_user, resident=resident1, is_allowed=True)
        data = {
            "resident_access": [
                {"resident": resident1.id, "is_allowed": True},
                {"resident": resident2.id, "is_allowed": False},
            ]
        }

        r = account_admin_client.patch(self.reverse(kwargs={"pk": user.pk}), data)
        h.responseOk(r)

        user_resident_access1 = UserResidentAccess.objects.get(resident=resident1)
        user_resident_access2 = UserResidentAccess.objects.get(resident=resident2)
        assert user_resident_access1.is_allowed is True
        assert user_resident_access2.is_allowed is False
