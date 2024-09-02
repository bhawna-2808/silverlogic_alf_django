import pytest

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestCloudCareResidentViewSet(ApiMixin):
    view_list = "cloudcare-residents-list"
    view_detail = "cloudcare-residents-detail"
    view_name = view_list

    def test_guest_cant_create(self, client):
        r = client.post(self.reverse())
        h.responseUnauthorized(r)

    def test_guest_cant_list(self, client):
        r = client.get(self.reverse())
        h.responseUnauthorized(r)

    def test_guest_cant_view(self, client):
        self.view_name = self.view_detail
        resident = f.ResidentFactory()
        r = client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseUnauthorized(r)

    def test_guest_cant_edit(self, client):
        self.view_name = self.view_detail
        resident = f.ResidentFactory()
        r = client.patch(self.reverse(kwargs={"pk": resident.pk}), {"first_name": "John"})
        h.responseUnauthorized(r)

    def test_cloudcare_user_can_create_resident(self, cloudcare_client):
        facility = f.FacilityFactory()
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1995-03-04",
            "sex": "m",
            "ssn": "111-22-2222",
            "facility": facility.pk,
            "primary_insurance": "MediCare",
            "insurance_relationship": "self",
            "insured_first_name": "John",
            "insured_last_name": "Doe",
            "insurance_policy_type": "primary",
            "insured_id": 123452,
        }

        r = cloudcare_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert r.data["first_name"] == data["first_name"]
        assert r.data["date_of_admission"] is not None

    def test_cloudcare_user_can_retreive_resident(self, cloudcare_client):
        self.view_name = self.view_detail
        resident = f.ResidentFactory()
        r = cloudcare_client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseOk(r)
        assert r.data["first_name"] == resident.first_name

    def test_user_can_list_resident(self, cloudcare_client):
        f.ResidentFactory.create_batch(size=3)
        f.ResidentFactory()
        r = cloudcare_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 4
