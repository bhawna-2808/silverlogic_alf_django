import pytest

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestCloudCareFacilityViewSet(ApiMixin):
    view_list = "cloudcare-positions-list"
    view_name = view_list

    def test_guest_cant_list(self, client):
        r = client.get(self.reverse())
        h.responseUnauthorized(r)

    def test_user_can_list_facilities(self, cloudcare_client):
        position = f.PositionFactory(name="Administrator")
        r = cloudcare_client.get(self.reverse())
        h.responseOk(r)
        assert r.data[0]["name"] == position.name
