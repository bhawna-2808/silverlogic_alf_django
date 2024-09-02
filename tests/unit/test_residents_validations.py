from datetime import date

from apps.residents.models import Resident
from apps.residents.validations import (
    missing_fields_for_examiner_signature,
    should_examiner_signature_be_deleted,
)


class TestMissingFieldsForExaminerSignature:
    def test_always_required_fields_missing(self):
        resident = Resident()
        assert "height" in missing_fields_for_examiner_signature(resident)

    def test_always_required_fields_not_missing(self):
        resident = Resident(height="123 inches")
        assert "height" not in missing_fields_for_examiner_signature(resident)

    def test_status_with_comments_fields_when_comment_not_required(self):
        resident = Resident(ambulation_status=Resident.Section1AChoices.independent)
        assert "ambulation_comments" not in missing_fields_for_examiner_signature(resident)

    def test_boolean_with_comments_fields_when_comment_not_required(self):
        resident = Resident(has_communicable_disease=False)
        assert "has_communicable_disease_comments" not in missing_fields_for_examiner_signature(
            resident
        )

    def test_examination_date(self):
        resident = Resident(examination_date=date(2016, 1, 1))
        assert "examination_date" not in missing_fields_for_examiner_signature(resident)

    def test_examiner_name(self, image_django_file):
        resident = Resident(examiner_signature=image_django_file)
        assert "examiner_name" in missing_fields_for_examiner_signature(resident)


class TestShouldExaminerSignatureBeDeleted(object):
    def test_when_field_is_changed(self, image_django_file):
        resident = Resident(height="124 inches", examiner_signature=image_django_file)
        resident_data = {"height": "125 inches"}
        assert should_examiner_signature_be_deleted(resident, resident_data)

    def test_when_no_fields_are_changed(self, image_django_file):
        resident = Resident(height="124 inches", examiner_signature=image_django_file)
        resident_data = {"height": "124 inches"}
        assert not should_examiner_signature_be_deleted(resident, resident_data)

    def test_when_field_is_not_present_in_data(self, image_django_file):
        resident = Resident(height="124 inches", examiner_signature=image_django_file)
        resident_data = {}
        assert not should_examiner_signature_be_deleted(resident, resident_data)

    def test_when_field_is_changed_but_resident_has_no_signature(self):
        resident = Resident(height="124 inches")
        resident_data = {"height": "125 inches"}
        assert not should_examiner_signature_be_deleted(resident, resident_data)

    def test_when_unchanged_field_is_date(self, image_django_file):
        resident = Resident(examination_date=date(2016, 1, 1), examiner_signature=image_django_file)
        resident_data = {"examination_date": "2016-01-01"}
        assert not should_examiner_signature_be_deleted(resident, resident_data)
