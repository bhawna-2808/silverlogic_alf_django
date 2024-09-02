from django.contrib.auth import get_user_model
from django.db import IntegrityError

import pytest
from mock import patch

from apps.examiners.models import Examiner, ResidentAccess
from apps.facilities.models import FacilityUser, UserInvite

import tests.factories as f

pytestmark = pytest.mark.django_db


class TestUserInvite(object):
    def test_only_one_invite_per_email_per_facility(self):
        facility = f.FacilityFactory()
        email = "john@example.com"
        f.UserInviteFactory(facility=facility, email=email)
        with pytest.raises(IntegrityError):
            f.UserInviteFactory(facility=facility, email=email)

    def test_email_is_sent_on_create(self):
        with patch.object(UserInvite, "send") as mock:
            f.UserInviteFactory()
            assert mock.called

    def test_email_is_not_sent_on_update(self):
        invite = f.UserInviteFactory()
        with patch.object(UserInvite, "send") as mock:
            invite.save()
            assert not mock.called

    def test_accept_creates_a_new_user(self):
        invite = f.UserInviteFactory()
        invite.accept(username="bob", password="1234", first_name="barb", last_name="walters")
        assert get_user_model().objects.filter(username="bob").exists()

    def test_accept_links_new_user_to_facility(self):
        invite = f.UserInviteFactory()
        invite.accept(username="bob", password="1234", first_name="barb", last_name="walters")
        assert FacilityUser.objects.filter(user__username="bob").exists()

    def test_accept_new_user_has_invite_role(self):
        invite = f.UserInviteFactory(role=UserInvite.Role.manager)
        invite.accept(username="bob", password="1234", first_name="barb", last_name="walters")
        assert FacilityUser.objects.get(user__username="bob").role == FacilityUser.Role.manager

    def test_accept_examiner_invite_creates_an_examiner(self):
        invite = f.UserInviteFactory(role=UserInvite.Role.examiner)
        invite.accept(
            username="bob",
            password="1234",
            first_name="barb",
            last_name="walters",
            medical_license_number="12345",
        )
        assert FacilityUser.objects.get(user__username="bob").role == FacilityUser.Role.examiner
        assert Examiner.objects.get().medical_license_number == "12345"

    def test_accept_examiner_creates_resident_access_using_invite_accesses(self):
        invite = f.UserInviteFactory(role=UserInvite.Role.examiner)
        f.UserInviteResidentAccessFactory(invite=invite)
        invite.accept(
            username="bob",
            password="1234",
            first_name="barb",
            last_name="walters",
            medical_license_number="12345",
        )
        assert FacilityUser.objects.get(user__username="bob").role == FacilityUser.Role.examiner
        assert Examiner.objects.get().medical_license_number == "12345"
        assert ResidentAccess.objects.count()
