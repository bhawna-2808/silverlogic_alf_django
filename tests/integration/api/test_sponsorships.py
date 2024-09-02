from datetime import date

import pytest
from dateutil.relativedelta import relativedelta

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestSponsorshipsList(ApiMixin):
    view_name = "sponsors-list"

    @pytest.fixture(autouse=True)
    def setup(self, employee_client):
        employee_client.facility.opted_in_sponsorship_date = date.today()
        employee_client.facility.sponsored_access = True
        employee_client.facility.save()
        self.employee_client = employee_client

    def test_guest_cant_list(self, client):
        r = client.get(self.reverse())
        h.responseUnauthorized(r)

    def test_employee_can_list(self, resident_and_staff_subscription):
        r = self.employee_client.get(self.reverse())
        h.responseOk(r)

    def test_list_sponsorship_from_same_facility(self, resident_and_staff_subscription):
        f.SponsorshipFactory(
            facility=f.FacilityFactory(
                name="Other facility",
                opted_in_sponsorship_date=date.today(),
                sponsored_access=True,
            )
        )
        sponsor = f.SponsorshipFactory(facility=self.employee_client.facility).sponsor
        r = self.employee_client.get(self.reverse())

        assert len(r.data) == 1
        assert r.data[0]["id"] == sponsor.id

    def test_nearby_facilities_calculation(self):
        from django.contrib.gis.geos import Point

        sponsor = f.SponsorFactory(point=Point(5, 23))
        f1 = f.FacilityFactory()
        f.ResidentFactory(facility=f1, is_active=False)
        f.ResidentFactory(facility=f1, is_active=True)
        assert sponsor.nearby_facilities.first().active_residents == 1

    def test_list_sponsorship_with_valid_dates(self, resident_and_staff_subscription):
        today = date.today()
        yesterday = today - relativedelta(days=1)
        tomorrow = today + relativedelta(days=1)

        # valid sponsorship
        sponsor = f.SponsorshipFactory(
            facility=self.employee_client.facility,
            start_date=yesterday,
        ).sponsor

        # sponsorship starts too late
        f.SponsorshipFactory(
            facility=self.employee_client.facility,
            start_date=tomorrow,
        )

        # sponsorship ends too early
        f.SponsorshipFactory(
            facility=self.employee_client.facility,
            start_date=yesterday,
            end_date=yesterday,
        )

        # sponsorship from another facility but with valid dates
        f.SponsorshipFactory(
            facility=f.FacilityFactory(
                name="Other facility",
                opted_in_sponsorship_date=date.today(),
                sponsored_access=True,
            ),
            start_date=yesterday,
        )

        r = self.employee_client.get(self.reverse())

        assert len(r.data) == 1
        assert r.data[0]["id"] == sponsor.id
