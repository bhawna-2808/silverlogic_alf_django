import pytest

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestResetPassword(ApiMixin):
    view_name = "user-reset-password"

    def test_guest_can_reset_password(self, client):
        data = {"email": "dev@tsl.io"}
        r = client.post(self.reverse(), data)
        h.responseNoContent(r)

    def test_duplicated_email(self, client, outbox):
        f.UserFactory.create_batch(size=2, email="dev@tsl.io")
        data = {"email": "dev@tsl.io"}
        r = client.post(self.reverse(), data)
        h.responseNoContent(r)
        assert len(outbox) == 2
