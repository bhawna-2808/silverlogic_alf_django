from datetime import datetime

import pytest
from constance import config
from freezegun import freeze_time

import tests.factories as f

pytestmark = pytest.mark.django_db


class TestSponsored(object):
    def test_facility_sponsored_changes_after_constance_time(self):
        with freeze_time(datetime(2019, 12, 1)):
            facility = f.FacilityFactory.build()
            assert facility.sponsored_access is False

        with freeze_time(config.SPONSORSHIPS_START):
            facility = f.FacilityFactory.build()
            assert facility.sponsored_access is True


class TestFacilityUser(object):
    def test_str(self):
        facility_user = f.FacilityUserFactory.build()
        assert str(facility_user)

    def test_repr(self):
        facility_user = f.FacilityUserFactory.build()
        assert repr(facility_user)


class TestUserInvite(object):
    def test_str(self):
        invite = f.UserInviteFactory.build()
        assert str(invite)

    def test_repr(self):
        invite = f.UserInviteFactory.build()
        assert repr(invite)

    def test_send_sends_an_email(self, outbox):
        invite = f.UserInviteFactory.build(id=1)
        invite.send()
        assert len(outbox) == 1
        assert outbox[0].to == [invite.email]

    def test_email_contains_inviters_name(self, outbox):
        invite = f.UserInviteFactory.build(
            id=1, invited_by__first_name="Sally", invited_by__last_name="May"
        )
        invite.send()
        assert "Sally May" in outbox[0].body

    def test_email_contains_facility_name(self, outbox):
        invite = f.UserInviteFactory.build(id=1, facility__name="John Robsons Angels")
        invite.send()
        assert "John Robsons Angels" in outbox[0].body

    def test_email_contains_role(self, outbox):
        invite = f.UserInviteFactory.build(id=1)
        invite.send()
        assert "Manager" in outbox[0].body
