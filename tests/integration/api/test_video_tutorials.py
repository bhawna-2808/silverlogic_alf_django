import pytest

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestTutorialVideosList(ApiMixin):
    view_name = "tutorial-videos-list"

    def test_guest_can_list(self, client):
        r = client.get(self.reverse())
        h.responseOk(r)

    def test_account_admin_can_list(self, account_admin_client):
        f.TutorialVideoFactory(url="https://www.youtube.com/watch?v=H11s_dbHbCA")
        f.TutorialVideoFactory(url="https://tsl-2.wistia.com/medias/2lqmcwz33p")
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 2

    def test_returns_embed_urls(self, account_admin_client):
        f.TutorialVideoFactory(url="https://www.youtube.com/watch?v=H11s_dbHbCA")
        f.TutorialVideoFactory(url="https://tsl-2.wistia.com/medias/2lqmcwz33p")
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)
        assert "embed" in r.data[0]["url"]
        assert "embed" in r.data[1]["url"]
