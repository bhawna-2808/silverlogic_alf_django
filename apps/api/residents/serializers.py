from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from apps.api.fields import PDFBase64File
from apps.api.mixins import DynamicFieldsMixin
from apps.api.serializers import ModelSerializer
from apps.examiners.models import ExaminationRequest
from apps.residents.models import (
    Archived1823,
    MedicationFile,
    Resident,
    ResidentBedHold,
    ResidentMedication,
    ServiceOffered,
)
from apps.residents.validations import (
    can_examiner_sign,
    missing_fields_for_examiner_signature,
    should_examiner_signature_be_deleted,
)


class ResidentMedicationSerializer(ModelSerializer):
    class Meta:
        model = ResidentMedication
        fields = (
            "medication",
            "dosage",
            "directions_for_use",
            "route",
        )


class ServiceOfferedSerializer(ModelSerializer):
    class Meta:
        model = ServiceOffered
        fields = (
            "need_identified",
            "service_needed",
            "frequency_and_duration",
            "service_provider_name",
            "date_service_began",
        )


class ExaminerAccessSerializer(serializers.Serializer):
    examiners = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)

    def validate_examiners(self, examiners):
        for examiner in examiners:
            if examiner.facility_users.facility != self.context["request"].facility:
                raise serializers.ValidationError(
                    _("You cannot grant non-facility-examiners access to a resident.")
                )
        return examiners


class ResidentBedHoldSerializer(ModelSerializer):
    def validate(self, data):
        if "date_in" in data and data["date_in"] and data["date_out"] > data["date_in"]:
            raise serializers.ValidationError("Date in must be after Date out.")
        return data

    class Meta:
        model = ResidentBedHold
        fields = "__all__"


class ResidentCloudCareSerializer(ModelSerializer):
    class Meta:
        model = Resident
        fields = (
            "id",
            "first_name",
            "last_name",
            "date_of_birth",
            "sex",
            "date_of_admission",
            "ssn",
            "facility",
            "primary_insurance",
            "insurance_relationship",
            "insured_first_name",
            "insured_last_name",
            "insurance_relationship",
            "insurance_policy_type",
            "insured_id",
        )

    def create(self, validated_data):
        validated_data["date_of_admission"] = timezone.now().date()
        resident = super(ResidentCloudCareSerializer, self).create(validated_data)
        return resident


class MedicationFileSerializer(ModelSerializer):
    pdf_file = PDFBase64File()

    class Meta:
        model = MedicationFile
        fields = (
            "id",
            "name",
            "pdf_file",
            "resident",
        )
        extra_kwargs = {
            "resident": {"write_only": True},
        }


class ResidentSerializer(DynamicFieldsMixin, ModelSerializer):
    medications = ResidentMedicationSerializer(many=True, required=False)
    services_offered = ServiceOfferedSerializer(many=True, required=False)
    examination_requested = serializers.SerializerMethodField()
    primary_is_examiner = serializers.SerializerMethodField()
    primary_is_examiner_invited = serializers.SerializerMethodField()
    has_examiners_assigned = serializers.SerializerMethodField()
    medication_files = serializers.ListField(source="medication_files.all", required=False)

    class Meta:
        model = Resident
        fields = (
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
            "insurance_policy_type",
            "insurance_relationship",
            "mma_plan",
            "mma_number",
            "drug_plan_name",
            "drug_plan_number",
            "case_worker_first_name",
            "case_worker_last_name",
            "case_worker_phone",
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
            "dialysis_center",
            "dialysis_center_phone",
            "hospice_provider",
            "hospice_provider_phone",
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
            "examination_due_date",
            "examination_interval",
            "examination_requested",
            "primary_is_examiner",
            "primary_is_examiner_invited",
            "has_examiners_assigned",
            "is_cha",
            "medication_files",
        )
        read_only_fields = ("age",)
        extra_kwargs = {
            "avatar": {
                "sizes": {
                    "small": {"size": (70, 70), "crop": True},
                    "medium": {"size": (300, 300), "crop": False},
                }
            }
        }

    def to_internal_value(self, data):
        # workaround to allow invalid phone numbers bypass validation, but forbid
        # new invalid numbers to be added
        phones_to_skip = {}
        phone_fields = (
            "case_worker_phone",
            "contact_1_home_phone",
            "contact_1_mobile_phone",
            "contact_2_home_phone",
            "contact_2_mobile_phone",
            "examiner_phone",
            "primary_doctor_phone",
            "psychiatric_doctor_phone",
        )
        for field in phone_fields:
            value = data.get(field, None)
            if value and value == getattr(self.instance, field, None):
                phones_to_skip[field] = data.pop(field)
        return_data = super().to_internal_value(data)
        return_data.update(phones_to_skip)
        return return_data

    def get_has_examiners_assigned(self, resident):
        return bool(len(resident.examiners.all()))

    def get_examination_requested(self, resident):
        for examination_request in resident.examination_requests.all():
            if examination_request.status == ExaminationRequest.Status.sent:
                return True
        return False

    def get_primary_is_examiner(self, resident):
        for ra in resident.examiners.all():
            if ra.examiner.user.email == resident.primary_doctor_email:
                return True
        return False

    def get_primary_is_examiner_invited(self, resident):
        for ra in resident.examiners.all():
            if ra.examiner.user.email == resident.primary_doctor_email:
                return False
        for ura in resident.user_invites.all():
            if ura.invite.email == resident.primary_doctor_email:
                return True
        return False

    def validate(self, data):
        examiner_signature = data.get("examiner_signature", None)
        if examiner_signature and not can_examiner_sign(resident=self.instance, resident_data=data):
            raise serializers.ValidationError(
                {
                    field_name: [
                        _("This field is required before the medical examination may be signed.")
                    ]
                    for field_name in missing_fields_for_examiner_signature(
                        resident=self.instance, resident_data=data
                    )
                }
            )
        if "date_of_admission" in data and data.get("date_of_admission") is None:
            raise serializers.ValidationError({"date_of_admission": "Cannot remove this value"})
        self.validate_diets(data)
        return data

    def validate_diets(self, data):
        if data.get("is_diet_regular", None) and any(
            [
                data.get("is_diet_calorie_controlled", None),
                data.get("is_diet_no_added_salt", None),
                data.get("is_diet_low_fat_or_low_cholesterol", None),
                data.get("is_diet_low_sugar", None),
                data.get("is_diet_other", None),
            ]
        ):
            raise serializers.ValidationError(
                {
                    "is_diet_regular": [
                        _("Diet can either be `is_diet_regular` OR special diet(s) but not both.")
                    ]
                }
            )

    def sync_medication_files(self, data):
        medication_files = data.pop("medication_files", None)
        if medication_files is None:
            return

        existent_files = []
        for medication_file in medication_files["all"]:
            if "id" in medication_file:
                existent_files.append(medication_file["id"])
                continue
            medication_file.update({"resident": self.instance.id})
            serializer = MedicationFileSerializer(data=medication_file)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            existent_files.append(instance.id)
        self.instance.medication_files.exclude(id__in=existent_files).delete()

    def create(self, validated_data):
        self.sync_medication_files(validated_data)
        validated_data["facility"] = self.context["request"].facility
        medications_data = validated_data.pop("medications", [])
        services_offered_data = validated_data.pop("services_offered", [])

        if (
            validated_data.get("long_term_care_provider") == ""
            and validated_data.get("long_term_care_number") == ""
        ):
            self.has_long_term_care_program = False

        self.set_is_active(validated_data)
        self.set_has_long_term_care_program(validated_data)
        resident = super(ResidentSerializer, self).create(validated_data)

        self.create_medications(resident, medications_data)
        self.create_services_offered(resident, services_offered_data)

        return resident

    def update(self, instance, validated_data):
        self.sync_medication_files(validated_data)
        if should_examiner_signature_be_deleted(instance, validated_data):
            instance.examiner_signature = None

        if "examiner_signature" in validated_data and (
            validated_data["examiner_signature"] != instance.examiner_signature
        ):
            examination_requests = instance.examination_requests.filter(
                status=ExaminationRequest.Status.sent
            )
            examination_requests.update(status=ExaminationRequest.Status.examined)

        if (
            validated_data.get("long_term_care_provider") == ""
            and validated_data.get("long_term_care_number") == ""
        ):
            instance.has_long_term_care_program = False

        medications_data = validated_data.pop("medications", None)
        services_offered_data = validated_data.pop("services_offered", None)

        self.set_is_active(validated_data)
        self.set_has_long_term_care_program(validated_data)
        resident = super(ResidentSerializer, self).update(instance, validated_data)

        if medications_data is not None:
            resident.medications.all().delete()
            self.create_medications(resident, medications_data)
        if services_offered_data is not None:
            resident.services_offered.all().delete()
            self.create_services_offered(resident, services_offered_data)
        return resident

    def set_is_active(self, validated_data):
        if validated_data.get("date_of_discharge", None) is None:
            validated_data["is_active"] = True
        if (
            validated_data.get("date_of_discharge")
            and validated_data["date_of_discharge"] <= timezone.now().date()
        ):
            validated_data["is_active"] = False

    def set_has_long_term_care_program(self, validated_data):
        validated_data["has_long_term_care_program"] = bool(
            validated_data.get("long_term_care_provider")
        )

    def create_medications(self, resident, medications_data):
        for medication_data in medications_data:
            resident.medications.create(**medication_data)

    def create_services_offered(self, resident, services_offered_data):
        for service_offered_data in services_offered_data:
            resident.services_offered.create(**service_offered_data)

    def to_representation(self, resident):
        data = super().to_representation(resident)
        if "medication_files" in data:
            data["medication_files"] = MedicationFileSerializer(
                data["medication_files"], many=True
            ).data
        return data


class Archived1823Serializer(ModelSerializer):
    class Meta:
        model = Archived1823
        fields = ["id", "date_archived", "date_signed"]
