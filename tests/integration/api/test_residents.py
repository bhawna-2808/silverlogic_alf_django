import base64
from datetime import timedelta

from django.test.utils import freeze_time
from django.utils import timezone

import mock
import pytest

from apps.activities.models import Activity
from apps.examiners.models import ExaminationRequest, ResidentAccess
from apps.residents.models import Archived1823, Resident, ResidentMedication, ServiceOffered
from apps.subscriptions.models import Plan, Subscription

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestResidentCreate(ApiMixin):
    view_name = "residents-list"

    @pytest.fixture
    def data(self):
        return {
            "first_name": "John",
            "last_name": "Smith",
        }

    def test_guest_cant_create(self, client, data):
        r = client.post(self.reverse(), data)
        h.responseUnauthorized(r)

    def test_admin_employee_can_create(
        self, account_admin_client, resident_and_staff_subscription, data
    ):
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert Resident.objects.count() == 1

    def test_resident_creation_is_tracked(
        self, account_admin_client, resident_and_staff_subscription, data
    ):
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert Resident.objects.count() == 1
        assert Activity.objects.count() == 1
        activity = Activity.objects.get()
        resident = Resident.objects.get()
        assert activity.actor == account_admin_client.user
        assert activity.verb == "created resident"
        assert activity.action_object == resident
        assert activity.target == account_admin_client.facility

    def test_examiner_cant_create(self, examiner_client, resident_and_staff_subscription, data):
        r = examiner_client.post(self.reverse(), data)
        h.responseForbidden(r)

    def test_trainings_user_cant_create(
        self, trainings_user_client, resident_and_staff_subscription, data
    ):
        r = trainings_user_client.post(self.reverse(), data)
        h.responseForbidden(r)

    def test_facility_is_same_as_user(
        self, account_admin_client, resident_and_staff_subscription, data
    ):
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert Resident.objects.get().facility == account_admin_client.facility

    def test_can_set_medications(self, account_admin_client, resident_and_staff_subscription, data):
        data["medications"] = [
            {
                "medication": "Gummy bears",
                "dosage": "12mg",
                "directions_for_use": "in the butt",
                "route": "sideways",
            },
            {
                "medication": "Hockey",
                "dosage": "2 games",
                "directions_for_use": "once per day",
                "route": "Quebec",
            },
        ]
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert ResidentMedication.objects.count() == 2

    def test_can_set_services_offered(
        self, account_admin_client, resident_and_staff_subscription, data
    ):
        data["services_offered"] = [
            {
                "need_identified": "no sense",
                "service_needed": "john",
                "frequency_and_duration": "daily",
                "service_provider_name": "tim",
                "date_service_began": "2016-01-01",
            },
        ]
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert ServiceOffered.objects.count() == 1

    def test_cant_create_with_examiner_signature_without_correct_fields_filled_out(
        self, account_admin_client, resident_and_staff_subscription, data, image_base64
    ):
        data["examiner_signature"] = image_base64
        r = account_admin_client.post(self.reverse(), data)
        h.responseBadRequest(r)
        assert "This field is required before the medical examination may be signed." == str(
            r.data["weight"][0]
        )

    def test_resident_is_active_if_discharge_date_in_the_future(
        self, account_admin_client, resident_and_staff_subscription, data
    ):
        data["date_of_discharge"] = timezone.now().date() + timedelta(days=2)
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert r.data["is_active"]

    def test_resident_is_inactive_if_discharge_date_in_the_past(
        self, account_admin_client, resident_and_staff_subscription, data
    ):
        data["date_of_discharge"] = timezone.now().date() - timedelta(days=2)
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert not r.data["is_active"]

    def test_resident_is_inactive_if_discharge_date_is_today(
        self, account_admin_client, resident_and_staff_subscription, data
    ):
        data["date_of_discharge"] = timezone.now().date()
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert not r.data["is_active"]

    def test_cant_set_both_is_diet_regular_and_special_diet(
        self, account_admin_client, resident_and_staff_subscription, data
    ):
        data["is_diet_regular"] = True
        data["is_diet_calorie_controlled"] = True
        r = account_admin_client.post(self.reverse(), data)
        h.responseBadRequest(r)
        assert (
            r.data["is_diet_regular"][0]
            == "Diet can either be `is_diet_regular` OR special diet(s) but not both."
        )

    def test_sets_has_long_term_care_program(
        self, account_admin_client, resident_and_staff_subscription, data
    ):
        data["has_long_term_care_program"] = False
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert r.data["has_long_term_care_program"] is False

        data["long_term_care_provider"] = "Some provider"
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert r.data["has_long_term_care_program"] is True

        data["long_term_care_provider"] = ""
        data["long_term_care_number"] = ""
        r = account_admin_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert r.data["has_long_term_care_program"] is False


class TestResidentsRetrieve(ApiMixin):
    view_name = "residents-detail"

    def test_guest_cant_retrieve(self, client):
        resident = f.ResidentFactory()
        r = client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseUnauthorized(r)

    def test_trainings_user_cant_retrieve(self, trainings_user_client):
        resident = f.ResidentFactory()
        r = trainings_user_client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseForbidden(r)

    def test_admin_employee_cant_retrieve_if_resident_is_in_other_facility(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory(facility__name="blarg")
        r = account_admin_client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseNotFound(r)

    def test_admin_employee_can_retrieve_if_resident_is_in_same_facility(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        r = account_admin_client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseOk(r)

    def test_examiner_can_retrieve_if_they_have_been_given_access(
        self, examiner_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        f.ResidentAccessFactory(examiner=examiner_client.examiner, resident=resident)
        r = examiner_client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseOk(r)

    def test_examiner_cant_retrieve_without_access(
        self, examiner_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        r = examiner_client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseNotFound(r)

    def test_examination_requested_returns_false_if_no_examination_requested(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        r = account_admin_client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseOk(r)
        assert r.data["examination_requested"] is False

    def test_examination_requested_returns_true_if_examination_requested(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        f.ExaminationRequestFactory(resident=resident)
        r = account_admin_client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseOk(r)
        assert r.data["examination_requested"] is True

    def test_primary_is_examiner_returns_true_if_primary_is_examiner(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        examiner = f.ExaminerFactory(user__email=resident.primary_doctor_email)
        f.ResidentAccessFactory(resident=resident, examiner=examiner)
        r = account_admin_client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseOk(r)
        assert r.data["primary_is_examiner"] is True

    def test_primary_is_examiner_invited_returns_true_if_primary_is_invited(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        invite = f.UserInviteFactory(email=resident.primary_doctor_email)
        f.UserInviteResidentAccessFactory(resident=resident, invite=invite)
        r = account_admin_client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseOk(r)
        assert r.data["primary_is_examiner_invited"] is True

    def test_has_examiners_assigned_returns_true_if_resident_has_examiners_assigned(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        examiner = f.ExaminerFactory()
        f.ResidentAccessFactory(resident=resident, examiner=examiner)
        r = account_admin_client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseOk(r)
        assert r.data["has_examiners_assigned"] is True

    def test_has_examiners_assigned_returns_false_if_resident_has_no_examiners_assigned(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        r = account_admin_client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseOk(r)
        assert r.data["has_examiners_assigned"] is False

    def test_object_keys(self, account_admin_client, resident_and_staff_subscription):
        resident = f.ResidentFactory()
        r = account_admin_client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseOk(r)
        expected = {
            "id",
            "first_name",
            "last_name",
            "avatar",
            "date_of_birth",
            "age",
            "sex",
            "marital_status",
            "is_active",
            "room_number",
            "bed",
            "race",
            "religion",
            "ssn",
            "date_of_admission",
            "admitted_from",
            "date_of_discharge",
            "discharged_to",
            "discharge_reason",
            "discharge_notes",
            "personal_notes",
            "examination_due_date",
            "examination_interval",
            "examination_requested",
            "contact_1_name",
            "contact_1_relationship",
            "contact_1_home_phone",
            "contact_1_mobile_phone",
            "contact_1_email",
            "contact_1_address",
            "contact_2_name",
            "contact_2_relationship",
            "contact_2_home_phone",
            "contact_2_mobile_phone",
            "contact_2_email",
            "contact_2_address",
            "primary_insurance",
            "primary_insurance_number",
            "medicaid_number",
            "mma_plan",
            "mma_number",
            "drug_plan_name",
            "drug_plan_number",
            "has_completed_1823_on_file",
            "form_1823_completed_date",
            "dnr_on_file",
            "diagnosis",
            "allergies",
            "long_term_care_provider",
            "long_term_care_provider_other",
            "long_term_care_number",
            "primary_doctor_name",
            "primary_doctor_phone",
            "permanent_placement",
            "primary_doctor_address",
            "primary_doctor_email",
            "psychiatric_doctor_name",
            "psychiatric_doctor_phone",
            "psychiatric_doctor_address",
            "psychiatric_doctor_email",
            "medical_notes",
            "has_signed_contract_on_file",
            "contract_amount",
            "has_durable_power_of_attorney_on_file",
            "has_long_term_care_program",
            "has_assistive_care_services",
            "has_oss",
            "financial_notes",
            "height",
            "weight",
            "physical_or_sensory_limitations",
            "cognitive_or_behavioral_status",
            "nursing_treatment_therapy_service_requirements",
            "special_precautions",
            "is_elopement_risk",
            "ambulation_status",
            "bathing_status",
            "dressing_status",
            "eating_status",
            "self_care_status",
            "toileting_status",
            "transferring_status",
            "is_diet_regular",
            "is_diet_calorie_controlled",
            "is_diet_no_added_salt",
            "is_diet_low_fat_or_low_cholesterol",
            "is_diet_low_sugar",
            "is_diet_other",
            "diet_other_comments",
            "has_communicable_disease",
            "has_communicable_disease_comments",
            "is_bedridden",
            "is_bedridden_comments",
            "has_pressure_sores",
            "has_pressure_sores_comments",
            "does_pose_danger",
            "does_pose_danger_comments",
            "requires_nursing_or_psychiatric_care",
            "requires_nursing_or_psychiatric_care_comments",
            "can_needs_be_met",
            "can_needs_be_met_comments",
            "section_2_a_other_name",
            "section_2_a_other_status",
            "section_2_a_other_comments",
            "section_2_b_other1_name",
            "section_2_b_other1_status",
            "section_2_b_other1_comments",
            "section_2_b_other2_name",
            "section_2_b_other2_status",
            "section_2_b_other2_comments",
            "section_2_b_other3_name",
            "section_2_b_other3_status",
            "section_2_b_other3_comments",
            "section_2_b_other4_name",
            "section_2_b_other4_status",
            "section_2_b_other4_comments",
            "additional_comments_or_observations",
            "medications",
            "requires_help_taking_medication",
            "is_dialysis_patient",
            "is_under_hospice_care",
            "requires_help_with_self_administered_medication",
            "requires_medication_administration",
            "is_able_to_administer_without_assistance",
            "section_2_b_additional_comments",
            "signature_on_file",
            "examiner_name",
            "examiner_signature",
            "examiner_medical_license_number",
            "examiner_address",
            "examiner_phone",
            "examiner_title",
            "examination_date",
            "services_offered",
            "case_worker_first_name",
            "case_worker_last_name",
            "case_worker_phone",
            "dialysis_center",
            "dialysis_center_phone",
            "hospice_provider",
            "hospice_provider_phone",
            "primary_is_examiner_invited",
            "primary_is_examiner",
            "has_examiners_assigned",
            "is_cha",
            "insurance_relationship",
            "insurance_policy_type",
            "medication_files",
        }
        actual = set(r.data.keys())
        assert expected == actual


class TestResidentsUpdate(ApiMixin):
    view_name = "residents-detail"

    def test_guest_cant_update(self, client):
        resident = f.ResidentFactory()
        r = client.patch(self.reverse(kwargs={"pk": resident.pk}))
        h.responseUnauthorized(r)

    def test_trainings_user_cant_update(self, trainings_user_client):
        resident = f.ResidentFactory()
        r = trainings_user_client.patch(self.reverse(kwargs={"pk": resident.pk}))
        h.responseForbidden(r)

    def test_admin_employee_cant_update_if_resident_is_in_other_facility(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory(facility__name="blarg")
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}))
        h.responseNotFound(r)

    def test_admin_employee_can_update_if_resident_is_in_same_facility(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}))
        h.responseOk(r)

    def test_can_update_medications_list(
        self, account_admin_client, resident_and_staff_subscription, pdf_file
    ):
        resident = f.ResidentFactory()
        data = {
            "medication_files": [
                {
                    "name": "AttachmentMeds",
                    "pdf_file": base64.b64encode(pdf_file),
                }
            ]
        }
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)

        medication_file = resident.medication_files.get()
        assert medication_file.name == "AttachmentMeds"

    def test_ignore_update_medications_list_if_id_is_sent(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        medication_file = f.ResidentMedicationFileFactory(resident=resident)
        data = {
            "medication_files": [
                {
                    "id": medication_file.id,
                }
            ]
        }
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)

        m_file = resident.medication_files.get()
        assert m_file.name == medication_file.name

    def test_remove_medications_list_not_included(
        self, account_admin_client, resident_and_staff_subscription, pdf_file
    ):
        resident = f.ResidentFactory()
        to_be_removed_id = f.ResidentMedicationFileFactory(resident=resident).id
        medication_file = f.ResidentMedicationFileFactory(resident=resident)
        data = {
            "medication_files": [
                {
                    "id": medication_file.id,
                },
                {
                    "name": "AttachmentMeds.pdf",
                    "pdf_file": base64.b64encode(pdf_file),
                },
            ]
        }
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)
        assert resident.medication_files.count() == 2
        assert resident.medication_files.filter(id=to_be_removed_id).exists() is False

    def test_can_update_medications_file(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        f.ResidentMedicationFactory(resident=resident)
        data = {
            "medications": [
                {
                    "medication": "fruit loops",
                    "dosage": "500 loops",
                    "directions_for_use": "eat em",
                    "route": "spoon",
                }
            ]
        }
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)
        assert ResidentMedication.objects.count() == 1
        assert ResidentMedication.objects.get().medication == "fruit loops"

    def test_can_update_services_offered(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        f.ServiceOfferedFactory(resident=resident)
        data = {
            "services_offered": [
                {
                    "need_identified": "hungry",
                    "service_needed": "feed",
                    "frequency_and_duration": "3 times per day",
                    "service_provider_name": "Tony",
                    "date_service_began": "2016-01-02",
                }
            ]
        }
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)
        assert ServiceOffered.objects.count() == 1
        assert ServiceOffered.objects.get().need_identified == "hungry"

    def test_cant_update_with_examiner_signature_without_correct_fields_filled_out(
        self, account_admin_client, resident_and_staff_subscription, image_base64
    ):
        resident = f.ResidentFactory()
        data = {"examiner_signature": image_base64}
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseBadRequest(r)
        assert (
            "This field is required before the medical examination may be signed."
            == r.data["weight"][0]
        )

    def test_can_update_with_signature_on_file(
        self, account_admin_client, resident_and_staff_subscription, image_base64
    ):
        resident = f.ResidentFactory()
        data = {"signature_on_file": True}
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)

    def test_examiner_signature_should_be_deleted_if_1823_field_changes(
        self, account_admin_client, resident_and_staff_subscription, image_django_file
    ):
        resident = f.ResidentFactory(
            examiner_signature=image_django_file, examination_date=timezone.now().date()
        )
        data = {"height": "55 feet"}
        with mock.patch("apps.residents.models.generate_pdf"):
            r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
            h.responseOk(r)
            assert not r.data["examiner_signature"]

    def test_1823_archive_should_be_created_if_examiner_signature_changes(
        self, account_admin_client, resident_and_staff_subscription, image_django_file
    ):
        resident = f.ResidentFactory(
            examiner_signature=image_django_file, examination_date=timezone.now().date()
        )
        data = {"height": "55 feet"}
        with mock.patch("apps.residents.models.generate_pdf"):
            r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
            h.responseOk(r)
            archives = Archived1823.objects.filter(resident=resident)
            assert archives.count() == 1

    def test_resident_is_active_if_discharge_date_in_the_future(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        data = {"date_of_discharge": timezone.now().date() + timedelta(days=2)}
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)
        assert r.data["is_active"]

    def test_resident_is_inactive_if_discharge_date_in_the_past(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        data = {"date_of_discharge": timezone.now().date() - timedelta(days=2)}
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)
        assert not r.data["is_active"]

    def test_resident_is_inactive_if_discharge_date_is_today(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        data = {"date_of_discharge": timezone.now().date()}
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)
        assert not r.data["is_active"]

    def test_cant_set_both_is_diet_regular_and_special_diet(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        data = {"is_diet_regular": True, "is_diet_calorie_controlled": True}
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseBadRequest(r)
        assert (
            r.data["is_diet_regular"][0]
            == "Diet can either be `is_diet_regular` OR special diet(s) but not both."
        )

    def test_requests_should_be_set_to_examined_if_examiner_signature_changes(
        self, account_admin_client, resident_and_staff_subscription, image_base64
    ):
        resident = f.ResidentFactory()
        f.ExaminationRequestFactory(resident=resident)
        f.ExaminationRequestFactory(resident=resident)
        data = {"examiner_signature": image_base64}
        with mock.patch(
            "apps.api.residents.serializers.ResidentSerializer.run_validation",
            return_value=resident.__dict__,
        ):
            r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
            h.responseOk(r)
            requests = ExaminationRequest.objects.filter(
                resident=resident, status=ExaminationRequest.Status.sent
            )
            assert requests.count() == 0

    def test_update_long_term_care_program(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory(has_long_term_care_program=True)
        data = {
            "long_term_care_provider": "",
            "has_long_term_care_program": True,
            "long_term_care_number": "",
        }
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)
        assert r.data["has_long_term_care_program"] is False

    def test_update_cha_status(self, account_admin_client, resident_and_staff_subscription):
        resident = f.ResidentFactory(is_cha=False)
        data = {"is_cha": True}
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)
        assert r.data["is_cha"] is True

    def test_update_insurance_relationship_policy_type(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory(is_cha=False)
        assert resident.insurance_policy_type is None
        assert resident.insurance_relationship is None
        data = {"insurance_policy_type": "primary", "insurance_relationship": "self"}
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)
        assert r.data["insurance_policy_type"] == "primary"
        assert r.data["insurance_relationship"] == "self"
        data = {"insurance_policy_type": "", "insurance_relationship": ""}
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)
        assert r.data["insurance_policy_type"] == ""
        assert r.data["insurance_relationship"] == ""

    @freeze_time("2020-11-20")
    def test_resident_is_active_if_discharge_date_is_removed(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory(date_of_discharge=None)
        data = {"date_of_discharge": "2020-11-19"}
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)
        resident.refresh_from_db()
        data = {"date_of_discharge": None}
        assert resident.is_active is False
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        resident.refresh_from_db()
        assert resident.is_active is True

    def test_resident_admission_date_cant_be_deleted(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory(date_of_admission="2020-01-01")
        data = {"date_of_admission": "None"}
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseBadRequest(r)

    def test_resident_admission_date_can_be_modified(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory(date_of_admission="2020-01-01")
        data = {"date_of_admission": "2020-02-02"}
        r = account_admin_client.patch(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)


class TestResidentsDelete(ApiMixin):
    view_name = "residents-detail"

    def test_guest_cant_delete(self, client):
        resident = f.ResidentFactory()
        r = client.delete(self.reverse(kwargs={"pk": resident.pk}))
        h.responseUnauthorized(r)

    def test_trainings_user_cant_delete(self, trainings_user_client):
        resident = f.ResidentFactory()
        r = trainings_user_client.delete(self.reverse(kwargs={"pk": resident.pk}))
        h.responseForbidden(r)

    def test_admin_employee_cant_delete_if_resident_is_in_other_facility(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory(facility__name="blarg")
        r = account_admin_client.delete(self.reverse(kwargs={"pk": resident.pk}))
        h.responseNotFound(r)

    def test_admin_employee_can_delete_if_resident_is_in_same_facility(
        self, account_admin_client, resident_and_staff_subscription
    ):
        resident = f.ResidentFactory()
        r = account_admin_client.delete(self.reverse(kwargs={"pk": resident.pk}))
        h.responseNoContent(r)

    def test_examiner_cant_delete(self, examiner_client, resident_and_staff_subscription):
        resident = f.ResidentFactory()
        r = examiner_client.delete(self.reverse(kwargs={"pk": resident.pk}))
        h.responseForbidden(r)


class TestResidentsList(ApiMixin):
    view_name = "residents-list"

    def test_guest_cant_list(self, client):
        r = client.get(self.reverse())
        h.responseUnauthorized(r)

    def test_trainings_user_cant_list(self, trainings_user_client):
        r = trainings_user_client.get(self.reverse())
        h.responseForbidden(r)
        assert str(r.data["detail"]) == "You do not have permission to perform this action."

    def test_manager_cant_see_residents_if_not_allowed(
        self, manager_client, resident_and_staff_subscription
    ):
        facility_user = manager_client.user.facility_users
        facility_user.can_see_residents = False
        facility_user.save()

        r = manager_client.get(self.reverse())
        h.responseForbidden(r)

    def test_not_require_trial_staff_subscription_if_fcc_signup(self, account_admin_client):
        facility = account_admin_client.facility
        facility.fcc_signup = True
        facility.save()
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)

    def test_requires_residents_subscription(self, account_admin_client):
        f.SubscriptionFactory(
            facility=account_admin_client.facility,
            status=Subscription.Status.trialing,
            billing_interval__plan__module=Plan.Module.staff,
            trial_end=timezone.now() + timedelta(days=1),
        )
        r = account_admin_client.get(self.reverse())
        h.responseForbidden(r)
        assert r.data["detail"] == "no_resident_subscription"

    def test_excludes_residents_not_in_users_facility(
        self, account_admin_client, resident_and_staff_subscription
    ):
        f.ResidentFactory(facility__name="blarg")
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 0

    def test_includes_residents_in_users_facility(
        self, account_admin_client, resident_and_staff_subscription
    ):
        f.ResidentFactory()
        r = account_admin_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 1

    def test_filter_residents_for_managers(self, manager_client, resident_and_staff_subscription):
        visible_resident1 = f.ResidentFactory()  # Without UserResidentAccess instance
        visible_resident2 = f.ResidentFactory()  # With UserResidentAccess instance
        not_visible_resident = f.ResidentFactory()
        facility_user = manager_client.user.facility_users
        f.UserResidentAccessFactory(user=facility_user, resident=visible_resident2, is_allowed=True)
        f.UserResidentAccessFactory(
            user=facility_user, resident=not_visible_resident, is_allowed=False
        )

        r = manager_client.get(self.reverse())
        h.responseOk(r)

        assert len(r.data) == 2

        data_ids = [resident["id"] for resident in r.data]
        assert visible_resident1.id in data_ids
        assert visible_resident2.id in data_ids

    def test_can_limit_fields(self, account_admin_client, resident_and_staff_subscription):
        f.ResidentFactory()
        r = account_admin_client.get(self.reverse(query_params={"fields": "first_name,last_name"}))
        h.responseOk(r)
        assert set(r.data[0].keys()) == {"first_name", "last_name"}

    def test_filter_by_is_active_can_include_active_residents(
        self, account_admin_client, resident_and_staff_subscription
    ):
        f.ResidentFactory(is_active=True)
        r = account_admin_client.get(self.reverse(query_params={"is_active": True}))
        h.responseOk(r)
        assert len(r.data) == 1

    def test_filter_by_is_active_can_exclude_inactive_residents(
        self, account_admin_client, resident_and_staff_subscription
    ):
        f.ResidentFactory(is_active=False)
        r = account_admin_client.get(self.reverse(query_params={"is_active": True}))
        h.responseOk(r)
        assert len(r.data) == 0

    def test_search_by_full_name_includes_residents_whose_name_starts_with_the_search(
        self, account_admin_client, resident_and_staff_subscription
    ):
        f.ResidentFactory(first_name="john", last_name="smith")
        r = account_admin_client.get(self.reverse(query_params={"full_name": "john sm"}))
        h.responseOk(r)
        assert len(r.data) == 1

    def test_search_by_full_name_includes_residents_whose_name_is_the_search(
        self, account_admin_client, resident_and_staff_subscription
    ):
        f.ResidentFactory(first_name="john", last_name="smith")
        r = account_admin_client.get(self.reverse(query_params={"full_name": "john smith"}))
        h.responseOk(r)
        assert len(r.data) == 1

    def test_search_by_full_name_excludes_residents_whose_name_does_not_start_with_the_search(
        self, account_admin_client, resident_and_staff_subscription
    ):
        f.ResidentFactory(first_name="john", last_name="zoink")
        r = account_admin_client.get(self.reverse(query_params={"full_name": "john sm"}))
        h.responseOk(r)
        assert len(r.data) == 0

    def test_can_order_by_last_name(self, account_admin_client, resident_and_staff_subscription):
        resident1 = f.ResidentFactory(first_name="john", last_name="zoink")
        resident2 = f.ResidentFactory(first_name="john", last_name="smith")
        r = account_admin_client.get(
            self.reverse(query_params={"full_name": "john", "order_by": "last_name"})
        )
        h.responseOk(r)
        assert r.data[0]["last_name"] == resident2.last_name
        assert r.data[1]["last_name"] == resident1.last_name


class TestResidentsPDFList(ApiMixin):
    view_name = "residents-pdf"

    def test_account_admin_can_list(self, account_admin_client):
        r = account_admin_client.get(self.reverse())
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"

    def test_guest_cant_list(self, client):
        r = client.get(self.reverse())
        h.responseUnauthorized(r)


class TestResidentWillDeleteExaminerSignature(ApiMixin):
    view_name = "residents-will-delete-examiner-signature"

    def test_yes(self, account_admin_client, resident_and_staff_subscription, image_django_file):
        resident = f.ResidentFactory(examiner_signature=image_django_file)
        data = {"height": "123"}
        r = account_admin_client.post(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)
        assert r.data["result"]

    def test_no(self, account_admin_client, resident_and_staff_subscription, image_django_file):
        resident = f.ResidentFactory(examiner_signature=image_django_file)
        data = {"name": "tim bob"}
        r = account_admin_client.post(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)
        assert not r.data["result"]


class TestResidentExaminerAccessCreate(ApiMixin):
    view_name = "residents-examiner-access"

    def test_guest_cant_set(self, client):
        resident = f.ResidentFactory()
        r = client.post(self.reverse(kwargs={"pk": resident.pk}))
        h.responseUnauthorized(r)

    def test_trainings_user_cant_set(self, trainings_user_client):
        resident = f.ResidentFactory()
        r = trainings_user_client.post(self.reverse(kwargs={"pk": resident.pk}))
        h.responseForbidden(r)

    def test_account_admin_can_set(self, resident_and_staff_subscription, account_admin_client):
        resident = f.ResidentFactory()
        examiner = f.ExaminerFactory()
        f.FacilityUserFactory(user=examiner.user)
        data = {"examiners": [examiner.user.pk]}
        r = account_admin_client.post(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)

    def test_can_add_access(self, resident_and_staff_subscription, account_admin_client):
        resident = f.ResidentFactory()
        examiner = f.ExaminerFactory()
        f.FacilityUserFactory(user=examiner.user)
        data = {"examiners": [examiner.user.pk]}
        r = account_admin_client.post(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)
        assert ResidentAccess.objects.count() == 1

    def test_can_remove_access(self, resident_and_staff_subscription, account_admin_client):
        resident = f.ResidentFactory()
        f.ResidentAccessFactory(resident=resident)
        data = {"examiners": []}
        r = account_admin_client.post(self.reverse(kwargs={"pk": resident.pk}), data)
        h.responseOk(r)
        assert ResidentAccess.objects.count() == 0


class TestResidentExaminerAccessRetrieve(ApiMixin):
    view_name = "residents-examiner-access"

    def test_guest_cant_retrieve(self, client):
        resident = f.ResidentFactory()
        r = client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseUnauthorized(r)

    def test_trainings_user_cant_retrieve(self, trainings_user_client):
        resident = f.ResidentFactory()
        r = trainings_user_client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseForbidden(r)

    def test_account_admin_can_retrieve(
        self, resident_and_staff_subscription, account_admin_client
    ):
        resident = f.ResidentFactory()
        r = account_admin_client.get(self.reverse(kwargs={"pk": resident.pk}))
        h.responseOk(r)


class TestResidentRequestExaminationCreate(ApiMixin):
    view_name = "residents-request-examination"

    def test_guest_cant_create(self, client):
        resident = f.ResidentFactory()
        r = client.post(self.reverse(kwargs={"pk": resident.pk}))
        h.responseUnauthorized(r)

    def test_trainings_user_cant_create(self, trainings_user_client):
        resident = f.ResidentFactory()
        r = trainings_user_client.post(self.reverse(kwargs={"pk": resident.pk}))
        h.responseForbidden(r)

    def test_account_admin_can_create(self, resident_and_staff_subscription, account_admin_client):
        resident = f.ResidentFactory()
        r = account_admin_client.post(self.reverse(kwargs={"pk": resident.pk}))
        h.responseOk(r)

    def test_creates_requests_for_all_resident_examiners(
        self, resident_and_staff_subscription, account_admin_client
    ):
        resident = f.ResidentFactory()
        examiner = f.ExaminerFactory()
        examiner2 = f.ExaminerFactory()
        f.ResidentAccessFactory(resident=resident, examiner=examiner)
        f.ResidentAccessFactory(resident=resident, examiner=examiner2)
        r = account_admin_client.post(self.reverse(kwargs={"pk": resident.pk}))
        h.responseOk(r)
        assert ExaminationRequest.objects.count() == 2
