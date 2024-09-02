import pytest

from apps.examiners.models import ExaminationRequest, ResidentAccess

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestExaminerResidentAccessCreate(ApiMixin):
    view_name = "examiners-resident-access"

    def test_guest_cant_set(self, client):
        examiner = f.ExaminerFactory()
        r = client.post(self.reverse(kwargs={"user_id": examiner.user.pk}))
        h.responseUnauthorized(r)

    def test_non_account_admin_cant_set(self, manager_client):
        examiner = f.ExaminerFactory()
        r = manager_client.post(self.reverse(kwargs={"user_id": examiner.user.pk}))
        h.responseForbidden(r)

    def test_account_admin_cant_set_when_examiner_is_not_part_of_their_facility(
        self, account_admin_client
    ):
        examiner = f.ExaminerFactory()
        data = {"residents": []}
        r = account_admin_client.post(self.reverse(kwargs={"user_id": examiner.user.pk}), data)
        h.responseNotFound(r)

    def test_account_admin_can_set_when_examiner_is_part_of_their_facility(
        self, account_admin_client
    ):
        examiner = f.ExaminerFactory()
        f.FacilityUserFactory(user=examiner.user)
        data = {"residents": []}
        r = account_admin_client.post(self.reverse(kwargs={"user_id": examiner.user.pk}), data)
        h.responseOk(r)

    def test_can_add_access(self, account_admin_client):
        examiner = f.ExaminerFactory()
        f.FacilityUserFactory(user=examiner.user)
        resident = f.ResidentFactory()
        data = {"residents": [resident.pk]}
        r = account_admin_client.post(self.reverse(kwargs={"user_id": examiner.user.pk}), data)
        h.responseOk(r)
        assert ResidentAccess.objects.count() == 1

    def test_can_remove_access(self, account_admin_client):
        examiner = f.ExaminerFactory()
        f.FacilityUserFactory(user=examiner.user)
        f.ResidentAccessFactory(examiner=examiner)
        data = {"residents": []}
        r = account_admin_client.post(self.reverse(kwargs={"user_id": examiner.user.pk}), data)
        h.responseOk(r)
        assert ResidentAccess.objects.count() == 0

    def test_cant_add_access_for_residents_in_other_facilities(self, account_admin_client):
        examiner = f.ExaminerFactory()
        f.FacilityUserFactory(user=examiner.user)
        resident = f.ResidentFactory(facility__name="blakjsdflw")
        data = {"residents": [resident.pk]}
        r = account_admin_client.post(self.reverse(kwargs={"user_id": examiner.user.pk}), data)
        h.responseBadRequest(r)


class TestExaminerResidentAccessRetrieve(ApiMixin):
    view_name = "examiners-resident-access"

    def test_guest_cant_retrieve(self, client):
        examiner = f.ExaminerFactory()
        r = client.get(self.reverse(kwargs={"user_id": examiner.user.pk}))
        h.responseUnauthorized(r)

    def test_non_account_admin_cant_retrieve(self, manager_client):
        examiner = f.ExaminerFactory()
        r = manager_client.get(self.reverse(kwargs={"user_id": examiner.user.pk}))
        h.responseForbidden(r)

    def test_account_admin_cant_retrieve_when_examiner_is_not_part_of_their_facility(
        self, account_admin_client
    ):
        examiner = f.ExaminerFactory()
        r = account_admin_client.get(self.reverse(kwargs={"user_id": examiner.user.pk}))
        h.responseNotFound(r)

    def test_account_admin_can_retrieve_when_examiner_is_part_of_their_facility(
        self, account_admin_client
    ):
        examiner = f.ExaminerFactory()
        f.FacilityUserFactory(user=examiner.user)
        r = account_admin_client.get(self.reverse(kwargs={"user_id": examiner.user.pk}))
        h.responseOk(r)


class TestExaminationRequestCreate(ApiMixin):
    view_name = "examination-requests-list"

    def test_guest_cant_create(self, client):
        r = client.post(self.reverse())
        h.responseUnauthorized(r)

    def test_non_account_admin_cant_create(self, manager_client):
        r = manager_client.post(self.reverse())
        h.responseForbidden(r)

    def test_account_admin_cant_create_when_examiner_is_not_part_of_their_facility(
        self, account_admin_client
    ):
        examiner = f.ExaminerFactory()
        f.FacilityUserFactory(user=examiner.user, facility__name="blakjsdflw")
        resident = f.ResidentFactory()
        data = {"resident": resident.pk, "examiner": examiner.user.pk}
        r = account_admin_client.post(self.reverse(), data)
        h.responseBadRequest(r)
        assert (
            r.data["examiner"][0]
            == "You cannot request a non-facility-examiner to examine a resident."
        )

    def test_account_admin_cant_create_when_resident_is_not_part_of_their_facility(
        self, account_admin_client
    ):
        examiner = f.ExaminerFactory()
        f.FacilityUserFactory(user=examiner.user)
        resident = f.ResidentFactory(facility=f.FacilityFactory(name="blakjsdflw"))
        data = {"resident": resident.pk, "examiner": examiner.user.pk}
        r = account_admin_client.post(self.reverse(), data)
        h.responseBadRequest(r)
        assert (
            r.data["resident"][0]
            == "You cannot request an examination of a resident that is not in your facility."
        )

    def test_account_admin_cant_create_when_examiner_does_not_have_resident_access(
        self, account_admin_client
    ):
        examiner = f.ExaminerFactory()
        f.FacilityUserFactory(user=examiner.user)
        resident = f.ResidentFactory()
        data = {"resident": resident.pk, "examiner": examiner.user.pk}
        r = account_admin_client.post(self.reverse(), data)
        h.responseBadRequest(r)
        assert (
            r.data["non_field_errors"][0] == "The examiner does not have access to this resident."
        )

    def test_account_admin_cant_create_when_examination_already_requested(
        self, account_admin_client
    ):
        examiner = f.ExaminerFactory()
        f.FacilityUserFactory(user=examiner.user)
        resident = f.ResidentFactory()
        f.ResidentAccessFactory(resident=resident, examiner=examiner)
        f.ExaminationRequestFactory(resident=resident, examiner=examiner)
        data = {"resident": resident.pk, "examiner": examiner.user.pk}
        r = account_admin_client.post(self.reverse(), data)
        h.responseBadRequest(r)
        assert (
            r.data["non_field_errors"][0]
            == "The examiner has already been requested to examine this resident."
        )

    def test_account_admin_can_create(self, account_admin_client):
        examiner = f.ExaminerFactory()
        f.FacilityUserFactory(user=examiner.user)
        resident = f.ResidentFactory()
        f.ResidentAccessFactory(resident=resident, examiner=examiner)
        data = {"resident": resident.pk, "examiner": examiner.user.pk}
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert ExaminationRequest.objects.count() == 1

    def test_account_admin_can_create_when_examined_request_exists(self, account_admin_client):
        examiner = f.ExaminerFactory()
        f.FacilityUserFactory(user=examiner.user)
        resident = f.ResidentFactory()
        f.ResidentAccessFactory(resident=resident, examiner=examiner)
        f.ExaminationRequestFactory(
            resident=resident,
            examiner=examiner,
            status=ExaminationRequest.Status.examined,
        )
        data = {"resident": resident.pk, "examiner": examiner.user.pk}
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert ExaminationRequest.objects.count() == 2


class TestResidentExaminationRequestsList(ApiMixin):
    view_name = "examination-requests-list"

    def test_guest_cant_retrieve(self, client):
        r = client.get(self.reverse())
        h.responseUnauthorized(r)

    def test_account_admin_can_retrieve(self, subscription, account_admin_client):
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)

    def test_returns_examination_requests(self, subscription, account_admin_client):
        resident = f.ResidentFactory()
        examiner = f.ExaminerFactory()
        f.ExaminationRequestFactory(resident=resident, examiner=examiner)
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 1
        assert r.data[0]["examiner"] == examiner.user.pk

    def test_can_filter_by_resident(self, subscription, account_admin_client):
        resident = f.ResidentFactory()
        resident2 = f.ResidentFactory()
        examiner = f.ExaminerFactory()
        f.ExaminationRequestFactory(resident=resident, examiner=examiner)
        f.ExaminationRequestFactory(resident=resident2, examiner=examiner)
        r = account_admin_client.get(self.reverse(query_params={"resident": resident.pk}))
        h.responseOk(r)
        assert len(r.data) == 1
        assert r.data[0]["resident"] == resident.pk

    def test_can_filter_by_status(self, subscription, account_admin_client):
        resident = f.ResidentFactory()
        examiner = f.ExaminerFactory()
        f.ExaminationRequestFactory(
            resident=resident,
            examiner=examiner,
            status=ExaminationRequest.Status.examined,
        )
        f.ExaminationRequestFactory(resident=resident, examiner=examiner)
        r = account_admin_client.get(self.reverse(query_params={"status": "examined"}))
        h.responseOk(r)
        assert len(r.data) == 1
