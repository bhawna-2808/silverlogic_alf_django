import pytest

from apps.residents.tasks import EmailLTCFiles
from apps.trainings.models import Facility

import tests.factories as f

pytestmark = pytest.mark.django_db


class TestResident:
    def test_get_line(self):
        resident = f.ResidentFactory(
            date_of_birth="2000-01-31",
            date_of_admission="2021-01-31",
            date_of_discharge="2022-01-31",
            mma_number=123,
            mma_plan="mma_plan",
            is_cha=True,
            has_assistive_care_services=True,
            has_oss=True,
        )
        Facility.objects.update(capacity=10)
        resident.refresh_from_db()
        facility = resident.facility
        facility.refresh_from_db()
        bed_hold = f.ResidentBedHoldFactory(
            resident=resident,
            date_in="2021-02-08",
            date_out="2021-02-01",
        )
        bed_hold.refresh_from_db()

        line = EmailLTCFiles().get_line(resident, resident.facility, bed_hold)

        assert line[0] == resident.medicaid_number
        assert line[1] == resident.last_name
        assert line[2] == resident.first_name
        assert line[3] == resident.sex
        assert line[4] == "01/31/2000"
        assert line[5] == "01/31/2021"
        assert line[6] == "01/31/2022"
        assert line[7] == "02/01/2021"
        assert line[8] == "02/08/2021"
        assert line[9] == "7"
        assert line[10] == resident.discharge_reason
        assert line[11] == facility.name
        assert line[12] == "S"
        assert line[13] == resident.mma_plan
        assert line[14] == resident.mma_number
        assert line[15] == "Y"
        assert line[16] == "Y"
        assert line[17] == "Y"
        assert line[18] == facility.tax_id
        assert line[19] == facility.npi
        assert line[20] == "Y"
        assert line[21] == facility.capacity
        assert line[22] == 10 - 1  # capacity - active residents

    def test_get_admission_line(self):
        resident = f.ResidentFactory(admitted_from="Delray Medical Center")
        resident.refresh_from_db()
        amends = ["admission"]
        line = EmailLTCFiles().get_line(resident, resident.facility, None, amends)

        assert line[23] == resident.admitted_from
