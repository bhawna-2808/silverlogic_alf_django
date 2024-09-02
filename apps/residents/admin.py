from django.contrib import admin

from .models import (
    Archived1823,
    IlsFile,
    MedicationFile,
    Provider,
    ProviderEmail,
    ProviderFile,
    Resident,
    ResidentBedHold,
    ResidentMedication,
    ServiceOffered,
)


class ResidentMedicationInline(admin.TabularInline):
    model = ResidentMedication


class MedicationFileInline(admin.TabularInline):
    model = MedicationFile


class ServiceOfferedInline(admin.TabularInline):
    model = ServiceOffered


class ResidentBedHoldInline(admin.TabularInline):
    model = ResidentBedHold


class Archived1823Admin(admin.ModelAdmin):
    list_display = (
        "id",
        "date_signed",
        "date_archived",
        "resident",
        "data_archived",
    )
    search_fields = (
        "resident__first_name",
        "resident__last_name",
    )


class ProviderAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "position", "contact")
    search_fields = ("id", "name", "contact")


class ProviderEmailAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "provider")


class ProviderFileAdmin(admin.ModelAdmin):
    def provider_name(self, obj):
        return obj.provider.name

    list_display = ("id", "file", "provider_name")
    raw_id_fields = ("provider",)
    list_select_related = ("provider",)
    search_fields = ("id", "file", "provider__name")


class ResidentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "facility",
        "first_name",
        "last_name",
        "date_of_birth",
        "room_number",
        "bed",
        "is_active",
    )
    list_filter = (
        "sex",
        "marital_status",
        "is_active",
        "facility",
    )
    search_fields = (
        "first_name",
        "last_name",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "facility",
                    "first_name",
                    "last_name",
                    "avatar",
                    "date_of_birth",
                    "sex",
                    "marital_status",
                    "is_active",
                    "room_number",
                    "bed",
                    "race",
                    "religion",
                    "ssn",
                    "personal_notes",
                )
            },
        ),
        (
            "Contact",
            {
                "fields": (
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
                )
            },
        ),
        (
            "Insurance",
            {
                "fields": (
                    "primary_insurance",
                    "primary_insurance_number",
                    "medicaid_number",
                    "mma_plan",
                    "mma_number",
                    "drug_plan_name",
                    "drug_plan_number",
                    "insurance_policy_type",
                    "insurance_relationship",
                )
            },
        ),
        (
            "Medical",
            {
                "fields": (
                    "has_completed_1823_on_file",
                    "form_1823_completed_date",
                    "dnr_on_file",
                    "diagnosis",
                    "allergies",
                    "long_term_care_provider",
                    "long_term_care_number",
                    "primary_doctor_name",
                    "primary_doctor_phone",
                    "primary_doctor_address",
                    "primary_doctor_email",
                    "psychiatric_doctor_name",
                    "psychiatric_doctor_phone",
                    "psychiatric_doctor_address",
                    "psychiatric_doctor_email",
                    "medical_notes",
                    (
                        "dialysis_center",
                        "dialysis_center_phone",
                    ),
                    (
                        "hospice_provider",
                        "hospice_provider_phone",
                    ),
                )
            },
        ),
        (
            "Financial",
            {
                "fields": (
                    "has_signed_contract_on_file",
                    "contract_amount",
                    "has_durable_power_of_attorney_on_file",
                    "has_long_term_care_program",
                    "has_assistive_care_services",
                    "has_oss",
                    "financial_notes",
                    (
                        "case_worker_first_name",
                        "case_worker_last_name",
                        "case_worker_phone",
                    ),
                )
            },
        ),
        (
            "Admission",
            {
                "fields": (
                    "date_of_admission",
                    "admitted_from",
                    "date_of_discharge",
                    "discharged_to",
                    "discharge_reason",
                    "discharge_notes",
                )
            },
        ),
        (
            "Form 1823 Section 1: Health Assessment",
            {
                "fields": (
                    ("height", "weight"),
                    "physical_or_sensory_limitations",
                    "cognitive_or_behavioral_status",
                    "nursing_treatment_therapy_service_requirements",
                    "special_precautions",
                    "is_elopement_risk",
                )
            },
        ),
        (
            "Form 1823 Section 1 A",
            {
                "description": "To what extent does the individual need supervision or assistance with the following?",
                "fields": (
                    ("ambulation_status",),
                    ("bathing_status",),
                    ("dressing_status",),
                    ("eating_status",),
                    ("self_care_status",),
                    ("toileting_status",),
                    ("transferring_status",),
                ),
            },
        ),
        (
            "Form 1823 Section 1 B",
            {
                "description": "Special Diet Instructions",
                "fields": (
                    "is_diet_regular",
                    "is_diet_calorie_controlled",
                    "is_diet_no_added_salt",
                    "is_diet_low_fat_or_low_cholesterol",
                    "is_diet_low_sugar",
                    ("is_diet_other", "diet_other_comments"),
                ),
            },
        ),
        (
            "Form 1823 Section 1 C",
            {
                "description": (
                    "Does the individual have any of the following conditions/requirements? If yes, "
                    "please include an explanation in the comments column. "
                ),
                "fields": (
                    (
                        "has_communicable_disease",
                        "has_communicable_disease_comments",
                    ),
                    (
                        "is_bedridden",
                        "is_bedridden_comments",
                    ),
                    (
                        "has_pressure_sores",
                        "has_pressure_sores_comments",
                    ),
                    (
                        "does_pose_danger",
                        "does_pose_danger_comments",
                    ),
                    (
                        "requires_nursing_or_psychiatric_care",
                        "requires_nursing_or_psychiatric_care_comments",
                    ),
                ),
            },
        ),
        (
            "Form 1823 Section 1 D",
            {
                "fields": (
                    "can_needs_be_met",
                    "can_needs_be_met_comments",
                )
            },
        ),
        (
            "Form 1823 Section 2-A A",
            {
                "description": "Ability to perform self-care tasks",
                "fields": (
                    ("preparing_meals_status",),
                    ("shopping_status",),
                    ("making_phone_call_status",),
                    ("handling_personal_affairs_status",),
                    ("handling_financial_affairs_status",),
                    (
                        "section_2_a_other_name",
                        "section_2_a_other_status",
                        "section_2_a_other_comments",
                    ),
                ),
            },
        ),
        (
            "Form 1823 Section 2-A B",
            {
                "description": "General oversight",
                "fields": (
                    ("observing_wellbeing_status",),
                    ("observing_whereabouts_status",),
                    ("reminders_for_important_tasks_status",),
                    (
                        "section_2_b_other1_name",
                        "section_2_b_other1_status",
                        "section_2_b_other1_comments",
                    ),
                    (
                        "section_2_b_other2_name",
                        "section_2_b_other2_status",
                        "section_2_b_other2_comments",
                    ),
                    (
                        "section_2_b_other3_name",
                        "section_2_b_other3_status",
                        "section_2_b_other3_comments",
                    ),
                    (
                        "section_2_b_other4_name",
                        "section_2_b_other4_status",
                        "section_2_b_other4_comments",
                    ),
                ),
            },
        ),
        (
            "Form 1823 Section 2-A C",
            {"fields": ("additional_comments_or_observations",)},
        ),
        (
            "Form 1823 Section 2-B B",
            {
                "fields": (
                    "requires_help_taking_medication",
                    "requires_help_with_self_administered_medication",
                    "requires_medication_administration",
                    "is_able_to_administer_without_assistance",
                    "is_dialysis_patient",
                    "is_under_hospice_care",
                )
            },
        ),
        ("Form 1823 Section 2-B C", {"fields": ("section_2_b_additional_comments",)}),
        (
            "Form 1823 Medical Examination Information",
            {
                "fields": (
                    "signature_on_file",
                    "examiner_name",
                    "examiner_signature",
                    "examiner_medical_license_number",
                    "examiner_address",
                    "examiner_phone",
                    "examiner_title",
                    "examination_date",
                )
            },
        ),
        (
            "Form 1823 Section 3",
            {
                "description": "Services offered or arranged by the facility for the resident",
                "fields": (
                    "gaurdian_or_recipient_name",
                    "gaurdian_or_recipient_signature",
                    "administrator_or_designee_name",
                    "administrator_or_designee_signature",
                ),
            },
        ),
    )
    inlines = [
        MedicationFileInline,
        ResidentMedicationInline,
        ServiceOfferedInline,
        ResidentBedHoldInline,
    ]


admin.site.register(Archived1823, Archived1823Admin)
admin.site.register(Resident, ResidentAdmin)
admin.site.register(ResidentBedHold)
admin.site.register(IlsFile)
admin.site.register(Provider, ProviderAdmin)
admin.site.register(ProviderEmail, ProviderEmailAdmin)
admin.site.register(ProviderFile, ProviderFileAdmin)
