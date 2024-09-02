from datetime import date, datetime

import dateutil.parser


def can_examiner_sign(resident=None, resident_data=None):
    return not bool(missing_fields_for_examiner_signature(resident, resident_data))


def should_examiner_signature_be_deleted(resident, resident_data):
    if not resident.examiner_signature:
        return False

    # Fields that, if changed, would wipe the signature.  Contains all 1823
    # fields from Section 1 to Section 2-B.C and the examiner fields, minus the examiner
    # signature field.
    field_names = [
        "diagnosis",
        "allergies",
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
        "observing_whereabouts_status",
        "observing_whereabouts_comments",
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
        "requires_help_taking_medication",
        "is_dialysis_patient",
        "is_under_hospice_care",
        "requires_help_with_self_administered_medication",
        "requires_medication_administration",
        "is_able_to_administer_without_assistance",
        "section_2_b_additional_comments",
        "examiner_name",
        "examiner_medical_license_number",
        "examiner_address",
        "examiner_phone",
        "examiner_title",
        "examination_date",
    ]
    for field_name in field_names:
        if field_name not in resident_data:
            continue

        resident_value = getattr(resident, field_name)
        data_value = resident_data[field_name]
        if isinstance(resident_value, datetime) and isinstance(data_value, str):
            data_value = dateutil.parser.parse(data_value)
        if isinstance(resident_value, date) and isinstance(data_value, str):
            data_value = dateutil.parser.parse(data_value).date()

        if resident_value != data_value:
            return True

    if "medications" in resident_data:
        medications = resident_data["medications"]
        if len(medications) != resident.medications.count():
            return True
        medications = sorted(medications, key=lambda x: (x["medication"], x["dosage"]))
        for i, medication in enumerate(resident.medications.order_by("medication", "dosage").all()):
            if medication.medication != medications[i]["medication"]:
                return True
            if medication.dosage != medications[i]["dosage"]:
                return True
            if medication.directions_for_use != medications[i]["directions_for_use"]:
                return True
            if medication.route != medications[i]["route"]:
                return True
    return False


def missing_fields(resident, resident_data, req_examiner_info):
    missing_fields = []

    always_required_fields = [
        "diagnosis",
        "allergies",
        "height",
        "weight",
        "physical_or_sensory_limitations",
        "cognitive_or_behavioral_status",
        "nursing_treatment_therapy_service_requirements",
        "special_precautions",
        "ambulation_status",
        "bathing_status",
        "dressing_status",
        "eating_status",
        "self_care_status",
        "toileting_status",
        "transferring_status",
        "examination_date",
    ]

    if req_examiner_info:
        examiner_info = [
            "examiner_name",
            "examiner_medical_license_number",
            "examiner_address",
            "examiner_phone",
            "examiner_title",
        ]
        always_required_fields.extend(examiner_info)

    for field_name in always_required_fields:
        if not get_field_value(field_name, resident, resident_data):
            missing_fields.append(field_name)

    return missing_fields


def missing_fields_for_examiner_signature(resident=None, resident_data=None):
    """What fields need to be filled out before an examiner can sign."""
    assert resident or resident_data

    return missing_fields(resident, resident_data, True)


def is_comment_required(value):
    return value.endswith("*")


def get_field_value(field_name, resident, resident_data):
    if resident_data and field_name in resident_data:
        value = resident_data[field_name]
    elif resident:
        value = getattr(resident, field_name, None)
    else:
        value = None
    return value
