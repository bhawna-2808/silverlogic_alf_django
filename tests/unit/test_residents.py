from datetime import date

import mock
import pysftp
import pytest
from dateutil.relativedelta import relativedelta

from apps.residents.models import IlsFile, Resident
from apps.residents.utils import generate_new_ils_file, upload_ils_files

import tests.factories as f

pytestmark = pytest.mark.django_db


class TestResident:
    def test_str(self):
        resident = Resident(first_name="John", last_name="Smith")
        assert str(resident) == "John Smith"

    def test_repr(self):
        resident = Resident(pk=1)
        assert repr(resident) == "<Resident: 1>"

    def test_age(self):
        resident = Resident(date_of_birth=date(1995, 2, 27))
        assert resident.age

    def test_age_when_no_date_of_birth(self):
        resident = Resident()
        assert resident.age is None

    def test_examination_interval_when_new(self):
        resident = Resident()
        assert resident.examination_interval == 1

    def test_examination_interval_when_not_active(self):
        resident = Resident(is_active=False)
        assert resident.examination_interval is None

    def test_examination_interval_when_not_has_assistive_care_services(self):
        resident = Resident(signature_on_file=True)
        assert resident.examination_interval == 36

    def test_examination_interval_when_has_assistive_care_services(self):
        resident = Resident(signature_on_file=True, has_assistive_care_services=True)
        assert resident.examination_interval == 12

    def test_examination_due_date_when_new(self):
        date_of_admission = date.today()
        resident = Resident(date_of_admission=date_of_admission)
        assert resident.examination_due_date == resident.date_of_admission + relativedelta(months=1)

    def test_examination_due_date_when_not_active(self):
        resident = Resident(is_active=False)
        assert resident.examination_due_date == ""

    def test_examination_due_date_when_not_has_assistive_care_services(self):
        examination_date = date.today() - relativedelta(years=3)
        resident = Resident(signature_on_file=True, examination_date=examination_date)
        assert resident.examination_due_date == resident.examination_date + relativedelta(years=3)

    def test_examination_due_date_when_has_assistive_care_services(self):
        examination_date = date.today() - relativedelta(years=1)
        resident = Resident(
            signature_on_file=True,
            has_assistive_care_services=True,
            examination_date=examination_date,
        )
        assert resident.examination_due_date == resident.examination_date + relativedelta(years=1)


def test_generate_residents_ils_file(expected_ils_file):
    generate_new_ils_file()

    ils_file = IlsFile.objects.get()
    content = ils_file.generated_file.read()

    # on local content is bytes on cgi its a string
    assert (
        type(content) == bytes
        and content.decode("utf-8") == expected_ils_file
        or content == expected_ils_file
    )


@mock.patch.object(
    target=pysftp,
    attribute="Connection",
    autospec=True,
    return_value=mock.Mock(
        spec=pysftp.Connection,
        __enter__=lambda self: self,
        __exit__=lambda self, *args: self,
    ),
)
def test_upload_residents_ils_file(mock_pysftp, image_django_file):
    f.IlsFileFactory(generated_file=image_django_file)
    upload_ils_files()
