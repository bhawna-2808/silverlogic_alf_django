import pytest

import tests.factories as f

pytestmark = pytest.mark.django_db


class TestExaminer:
    def test_repr(self):
        examiner = f.ExaminerFactory.build()
        assert repr(examiner)

    def test_str(self):
        examiner = f.ExaminerFactory.build()
        assert str(examiner)


class TestResidentAccess:
    def test_repr(self):
        resident_access = f.ResidentAccessFactory.build()
        assert repr(resident_access)

    def test_str(self):
        resident_access = f.ResidentAccessFactory.build()
        assert str(resident_access)


class TestExaminationRequest:
    def test_repr(self):
        examination_request = f.ExaminationRequestFactory.build()
        assert repr(examination_request)

    def test_str(self):
        examination_request = f.ExaminationRequestFactory.build()
        assert str(examination_request)

    def test_send_sends_an_email(self, outbox):
        examination_request = f.ExaminationRequestFactory.build(id=1)
        examination_request.send()
        assert len(outbox) == 1
        assert outbox[0].to == [examination_request.examiner.user.email]

    def test_email_contains_facility_name(self, outbox):
        examination_request = f.ExaminationRequestFactory.build(
            id=1, resident__facility__name="John Robsons Angels"
        )
        examination_request.send()
        assert "John Robsons Angels" in outbox[0].body
