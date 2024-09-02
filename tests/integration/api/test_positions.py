import pytest

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestPositionRetrieve(ApiMixin):
    view_name = "position-detail"

    def test_guest_cant_retrieve(self, client):
        position = f.PositionFactory()
        r = client.get(self.reverse(kwargs={"pk": position.pk}))
        h.responseUnauthorized(r)

    def test_guest_can_retrieve(self, manager_client, resident_and_staff_subscription):
        position = f.PositionFactory()
        r = manager_client.get(self.reverse(kwargs={"pk": position.pk}))
        h.responseOk(r)


class TestPositionList(ApiMixin):
    view_name = "position-list"

    def test_guest_cant_list(self, client):
        f.PositionFactory()
        r = client.get(self.reverse())
        h.responseUnauthorized(r)
        assert len(r.data) == 1

    def test_user_can_list(self, manager_client, resident_and_staff_subscription):
        f.PositionFactory()
        r = manager_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 1


class TestPositionCreate(ApiMixin):
    view_name = "position-list"

    @pytest.fixture
    def data(self):
        return {
            "name": "Admin",
            "description": "Admin description",
            "responsibilities": [],
        }

    def test_guest_cant_create(self, data, client):
        r = client.post(self.reverse(), data)
        h.responseUnauthorized(r)

    def test_user_can_create(self, data, manager_client, resident_and_staff_subscription):
        r = manager_client.post(self.reverse(), data)
        h.responseCreated(r)
