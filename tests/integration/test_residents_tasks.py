from datetime import timedelta

from django.utils import timezone

import pytest
from dateutil.relativedelta import relativedelta

from apps.residents.tasks import email_resident_birthday_reminder, set_resident_is_active

import tests.factories as f

pytestmark = pytest.mark.django_db


class TestSetResidentIsActive(object):
    def test_sets_residents_inactive_who_are_discharged_today(self):
        resident = f.ResidentFactory(date_of_discharge=timezone.now().today())
        set_resident_is_active()
        resident.refresh_from_db()
        assert not resident.is_active

    def test_does_not_touch_residents_who_are_discharged_in_the_future(self):
        resident = f.ResidentFactory(date_of_discharge=timezone.now().today() + timedelta(days=1))
        set_resident_is_active()
        resident.refresh_from_db()
        assert resident.is_active

    def test_does_not_touch_residents_who_were_discharged_in_the_past(self):
        resident = f.ResidentFactory(date_of_discharge=timezone.now().today() - timedelta(days=1))
        set_resident_is_active()
        resident.refresh_from_db()
        assert resident.is_active


class TestEmailBirthdayEmailReminder(object):
    def test_sends_emails(self, outbox):
        birthday_tomorrow = (timezone.now() + relativedelta(days=1, years=-30)).date()
        facility = f.FacilityFactory()
        admin_position = f.PositionFactory(name="Administrator")

        f.EmployeeFactory(
            facility=facility,
            receives_emails=True,
            positions=[admin_position],
            email="admin@test.com",
        )
        resident = f.ResidentFactory(facility=facility, date_of_birth=birthday_tomorrow)

        email_resident_birthday_reminder()
        assert len(outbox) == 1
        assert outbox[0].to == ["admin@test.com"]
        assert resident.full_name in outbox[0].body
