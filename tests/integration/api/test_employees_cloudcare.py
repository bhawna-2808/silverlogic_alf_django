import pytest

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestCloudCareEmployeeViewSet(ApiMixin):
    view_list = "cloudcare-employees-list"
    view_detail = "cloudcare-employees-detail"
    view_name = view_list

    def test_guest_cant_create(self, client):
        r = client.post(self.reverse())
        h.responseUnauthorized(r)

    def test_guest_cant_list(self, client):
        r = client.get(self.reverse())
        h.responseUnauthorized(r)

    def test_guest_cant_view(self, client):
        self.view_name = self.view_detail
        employee = f.EmployeeFactory()
        r = client.get(self.reverse(kwargs={"pk": employee.pk}))
        h.responseUnauthorized(r)

    def test_guest_cant_edit(self, client):
        self.view_name = self.view_detail
        employee = f.EmployeeFactory()
        r = client.patch(self.reverse(kwargs={"pk": employee.pk}), {"first_name": "John"})
        h.responseUnauthorized(r)

    def test_cloudcare_user_can_create_employee(self, cloudcare_client):
        facility = f.FacilityFactory()
        position = f.PositionFactory()
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "facility": facility.pk,
            "positions": [position.pk],
        }

        r = cloudcare_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert r.data["first_name"] == data["first_name"]
        assert r.data["date_of_hire"] is not None

    def test_cloudcare_user_can_retreive_employee(self, cloudcare_client):
        self.view_name = self.view_detail
        employee = f.EmployeeFactory()
        r = cloudcare_client.get(self.reverse(kwargs={"pk": employee.pk}))
        h.responseOk(r)
        assert r.data["first_name"] == employee.first_name

    def test_user_can_list_employee(self, cloudcare_client):
        f.EmployeeFactory.create_batch(size=3)
        f.EmployeeFactory()
        r = cloudcare_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 4
