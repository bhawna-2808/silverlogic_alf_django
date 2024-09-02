from tempfile import TemporaryFile

from django.core.files import File
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from dateutil.relativedelta import relativedelta
from localflavor.us.models import USSocialSecurityNumberField
from model_utils import Choices, FieldTracker
from model_utils.models import TimeStampedModel

from apps.api.views import generate_pdf
from apps.base.models import UsPhoneNumberField, random_name_in

Sex = Choices(
    ("m", _("Male")),
    ("f", _("Female")),
    ("other", _("Other")),
)
MaritalStatus = Choices(
    ("single", _("Single")),
    ("married", _("Married")),
    ("divorced", _("Divorced")),
    ("widowed", _("Widowed")),
)
Race = Choices(
    ("white", _("White")),
    ("black", _("Black or African American")),
    ("latino", _("Hispanic/Latino")),
    ("asian", _("Asian")),
    ("other", _("Other")),
)


class Resident(models.Model):
    Section1AChoices = Choices(
        ("I", "independent", _("Independent")),
        ("S*", "needs_supervision", _("Needs Supervision *")),
        ("A*", "needs_assistance", _("Needs Assistance *")),
        ("T", "total_care", _("Total Care")),
    )
    Section2AChoices = Choices(
        ("I", "independent", _("Independent")),
        ("S*", "needs_supervision", _("Needs Supervision *")),
        ("A*", "needs_assistance", _("Needs Assistance *")),
    )
    Section2BChoices = Choices(
        ("I", "independent", _("Independent")),
        ("W", "weekly", _("Weekly")),
        ("D", "daily", _("Daily")),
        ("O*", "other", _("Other *")),
    )
    ExaminerTitle = Choices(
        ("md", _("MD")),
        ("do", _("DO")),
        ("arnp", _("ARNP")),
        ("pa", _("PA")),
    )
    InsuranceRelationship = Choices(
        ("self", _("Self")),
        ("spouse", _("Spouse")),
        ("other", _("Other")),
    )
    InsurancePolicyType = Choices(
        ("primary", _("Primary")),
        ("secondary", _("Secondary")),
        ("tertiary", _("Tertiary")),
    )

    facility = models.ForeignKey(
        "trainings.Facility", related_name="residents", on_delete=models.CASCADE
    )

    # Personal Details
    first_name = models.CharField(_("First Name"), max_length=255)
    last_name = models.CharField(_("Last Name"), max_length=255)
    avatar = models.ImageField(
        blank=True, null=True, upload_to=random_name_in("residents/resident-avatars")
    )
    date_of_birth = models.DateField(_("Date of Birth"), blank=True, null=True)
    sex = models.CharField(_("Sex"), max_length=255, choices=Sex, blank=True)
    marital_status = models.CharField(
        _("Marital status"), max_length=255, choices=MaritalStatus, blank=True
    )
    is_active = models.BooleanField(default=True)
    room_number = models.CharField(_("Room"), max_length=255, blank=True)
    bed = models.CharField(_("Bed"), max_length=255, blank=True)
    race = models.CharField(_("Race"), max_length=255, choices=Race, blank=True)
    religion = models.CharField(_("Religion"), max_length=255, blank=True)
    ssn = USSocialSecurityNumberField(_("Social Security Number"), blank=True)
    personal_notes = models.TextField(_("Personal notes"), blank=True)
    is_cha = models.BooleanField(default=False)

    # Contact
    contact_1_name = models.CharField(max_length=255, blank=True)
    contact_1_relationship = models.CharField(max_length=255, blank=True)
    contact_1_home_phone = UsPhoneNumberField(blank=True)
    contact_1_mobile_phone = UsPhoneNumberField(blank=True)
    contact_1_email = models.EmailField(blank=True)
    contact_1_address = models.CharField(max_length=255, blank=True)
    contact_2_name = models.CharField(max_length=255, blank=True)
    contact_2_relationship = models.CharField(max_length=255, blank=True)
    contact_2_home_phone = UsPhoneNumberField(blank=True)
    contact_2_mobile_phone = UsPhoneNumberField(blank=True)
    contact_2_email = models.EmailField(blank=True)
    contact_2_address = models.CharField(max_length=255, blank=True)

    # Insurance
    primary_insurance = models.CharField(max_length=255, blank=True)
    primary_insurance_number = models.CharField(max_length=255, blank=True)
    medicaid_number = models.CharField(max_length=255, blank=True)
    mma_plan = models.CharField(max_length=255, blank=True)
    mma_number = models.CharField(max_length=255, blank=True)
    drug_plan_name = models.CharField(max_length=255, blank=True)
    drug_plan_number = models.CharField(max_length=255, blank=True)
    insurance_relationship = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=InsuranceRelationship,
        default=None,
    )
    insurance_policy_type = models.CharField(
        max_length=255, blank=True, null=True, choices=InsurancePolicyType, default=None
    )
    insured_id = models.IntegerField(null=True)
    insured_first_name = models.CharField(
        _("Insured First Name"), max_length=255, blank=True, null=True
    )
    insured_last_name = models.CharField(
        _("Insured Last Name"), max_length=255, blank=True, null=True
    )

    # Medical
    has_completed_1823_on_file = models.BooleanField(default=False)
    form_1823_completed_date = models.DateField(blank=True, null=True)
    dnr_on_file = models.BooleanField(
        _("DNR on file"), default=False, help_text=_("Do not resuscitate.")
    )
    diagnosis = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    long_term_care_provider = models.CharField(_("Long Term Care Plan"), max_length=255, blank=True)
    long_term_care_provider_other = models.CharField(
        _("Long Term Care Plan"), max_length=255, blank=True
    )
    long_term_care_number = models.CharField(_("Long Term Care Plan #"), max_length=255, blank=True)
    primary_doctor_name = models.CharField(max_length=255, blank=True)
    primary_doctor_phone = UsPhoneNumberField(blank=True)
    primary_doctor_address = models.CharField(max_length=255, blank=True)
    primary_doctor_email = models.EmailField(blank=True)
    psychiatric_doctor_name = models.CharField(max_length=255, blank=True)
    psychiatric_doctor_phone = UsPhoneNumberField(blank=True)
    psychiatric_doctor_address = models.CharField(max_length=255, blank=True)
    psychiatric_doctor_email = models.EmailField(blank=True)
    medical_notes = models.TextField(blank=True)
    dialysis_center = models.CharField(_("Dialysis Center"), max_length=255, blank=True)
    dialysis_center_phone = UsPhoneNumberField(max_length=255, blank=True)
    hospice_provider = models.CharField(_("Hospice Provider"), max_length=255, blank=True)
    hospice_provider_phone = UsPhoneNumberField(max_length=255, blank=True)

    # Financial
    has_signed_contract_on_file = models.BooleanField(default=False)
    contract_amount = models.CharField(max_length=255, blank=True)
    has_durable_power_of_attorney_on_file = models.BooleanField(default=False)
    has_long_term_care_program = models.BooleanField(default=False)
    has_assistive_care_services = models.BooleanField(_("Status"), default=False)
    has_oss = models.BooleanField(default=False)
    financial_notes = models.TextField(blank=True)
    case_worker_first_name = models.CharField(max_length=255, blank=True)
    case_worker_last_name = models.CharField(max_length=255, blank=True)
    case_worker_phone = UsPhoneNumberField(max_length=255, blank=True)
    permanent_placement = models.BooleanField(default=True)

    # Admission
    date_of_admission = models.DateField(_("Date of Admission"), blank=True, null=True)
    admitted_from = models.CharField(max_length=255, blank=True)
    date_of_discharge = models.DateField(_("Date of Discharge"), blank=True, null=True)
    discharged_to = models.CharField(max_length=255, blank=True)
    discharge_reason = models.CharField(max_length=255, blank=True)
    discharge_notes = models.CharField(max_length=255, blank=True)

    # Form 1823
    # Some fields are not included here because they are already present in
    # the facesheet.

    # Section 1: Health Assessment
    height = models.CharField(_("Height"), max_length=255, blank=True)
    weight = models.CharField(_("Weight"), max_length=255, blank=True)
    physical_or_sensory_limitations = models.TextField(
        _("Physical or sensory limitations"), blank=True
    )
    cognitive_or_behavioral_status = models.TextField(
        _("Cognitive or behavioral status"), blank=True
    )
    nursing_treatment_therapy_service_requirements = models.TextField(
        _("Nursing/treatment/therapy service requirements"), blank=True
    )
    special_precautions = models.TextField(_("Special precautions"), blank=True)
    is_elopement_risk = models.BooleanField(default=False)

    # 1.A
    ambulation_status = models.CharField(max_length=2, choices=Section1AChoices, blank=True)
    bathing_status = models.CharField(max_length=2, choices=Section1AChoices, blank=True)
    dressing_status = models.CharField(max_length=2, choices=Section1AChoices, blank=True)
    eating_status = models.CharField(max_length=2, choices=Section1AChoices, blank=True)
    self_care_status = models.CharField(max_length=2, choices=Section1AChoices, blank=True)
    toileting_status = models.CharField(max_length=2, choices=Section1AChoices, blank=True)
    transferring_status = models.CharField(max_length=2, choices=Section1AChoices, blank=True)

    # 1.B
    is_diet_regular = models.BooleanField(default=False)
    is_diet_calorie_controlled = models.BooleanField(default=False)
    is_diet_no_added_salt = models.BooleanField(default=False)
    is_diet_low_fat_or_low_cholesterol = models.BooleanField(default=False)
    is_diet_low_sugar = models.BooleanField(default=False)
    is_diet_other = models.BooleanField(default=False)
    diet_other_comments = models.CharField(max_length=100, blank=True)

    # 1.C
    has_communicable_disease = models.BooleanField(default=False)
    has_communicable_disease_comments = models.CharField(_("Comments"), max_length=100, blank=True)
    is_bedridden = models.BooleanField(default=False)
    is_bedridden_comments = models.CharField(_("Comments"), max_length=100, blank=True)
    has_pressure_sores = models.BooleanField(default=False)
    has_pressure_sores_comments = models.CharField(_("Comments"), max_length=100, blank=True)
    does_pose_danger = models.BooleanField(default=False)
    does_pose_danger_comments = models.CharField(_("Comments"), max_length=100, blank=True)
    requires_nursing_or_psychiatric_care = models.BooleanField(default=False)
    requires_nursing_or_psychiatric_care_comments = models.CharField(
        _("Comments"), max_length=100, blank=True
    )

    # 1.D
    can_needs_be_met = models.BooleanField(
        default=False,
        help_text=_(
            "In your professional opinion, can this individual's needs be met in an "
            "assisted living facility, which is not a medical, nursing or "
            "psychiatric facility?"
        ),
    )
    can_needs_be_met_comments = models.TextField(blank=True)

    # Section 2-A: Self-care and general oversight assessment

    # Section 2-A.A
    preparing_meals_status = models.CharField(max_length=2, choices=Section2AChoices, blank=True)
    preparing_meals_comments = models.CharField(_("Comments"), max_length=100, blank=True)
    shopping_status = models.CharField(max_length=2, choices=Section2AChoices, blank=True)
    shopping_comments = models.CharField(_("Comments"), max_length=100, blank=True)
    making_phone_call_status = models.CharField(max_length=2, choices=Section2AChoices, blank=True)
    making_phone_call_comments = models.CharField(_("Comments"), max_length=100, blank=True)
    handling_personal_affairs_status = models.CharField(
        max_length=2, choices=Section2AChoices, blank=True
    )
    handling_personal_affairs_comments = models.CharField(_("Comments"), max_length=100, blank=True)
    handling_financial_affairs_status = models.CharField(
        max_length=2, choices=Section2AChoices, blank=True
    )
    handling_financial_affairs_comments = models.CharField(
        _("Comments"), max_length=100, blank=True
    )
    section_2_a_other_name = models.CharField(_("Other name"), max_length=100, blank=True)
    section_2_a_other_status = models.CharField(
        _("Status"), max_length=2, choices=Section2AChoices, blank=True
    )
    section_2_a_other_comments = models.CharField(_("Comments"), max_length=100, blank=True)

    # Section 2-A.B
    observing_wellbeing_status = models.CharField(
        max_length=2, choices=Section2BChoices, blank=True
    )
    observing_wellbeing_comments = models.CharField(_("Comments"), max_length=100, blank=True)
    observing_whereabouts_status = models.CharField(
        max_length=2, choices=Section2BChoices, blank=True
    )
    observing_whereabouts_comments = models.CharField(_("Comments"), max_length=100, blank=True)
    reminders_for_important_tasks_status = models.CharField(
        max_length=2, choices=Section2BChoices, blank=True
    )
    reminders_for_important_tasks_comments = models.CharField(
        _("Comments"), max_length=100, blank=True
    )
    section_2_b_other1_name = models.CharField(_("Other name"), max_length=100, blank=True)
    section_2_b_other1_status = models.CharField(
        _("Status"), max_length=2, choices=Section2BChoices, blank=True
    )
    section_2_b_other1_comments = models.CharField(_("Comments"), max_length=100, blank=True)
    section_2_b_other2_name = models.CharField(_("Other name"), max_length=100, blank=True)
    section_2_b_other2_status = models.CharField(
        _("Status"), max_length=2, choices=Section2BChoices, blank=True
    )
    section_2_b_other2_comments = models.CharField(_("Comments"), max_length=100, blank=True)
    section_2_b_other3_name = models.CharField(_("Other name"), max_length=100, blank=True)
    section_2_b_other3_status = models.CharField(
        _("Status"), max_length=2, choices=Section2BChoices, blank=True
    )
    section_2_b_other3_comments = models.CharField(_("Comments"), max_length=100, blank=True)
    section_2_b_other4_name = models.CharField(_("Other name"), max_length=100, blank=True)
    section_2_b_other4_status = models.CharField(
        _("Status"), max_length=2, choices=Section2BChoices, blank=True
    )
    section_2_b_other4_comments = models.CharField(_("Comments"), max_length=100, blank=True)

    # Section 2-A.C
    additional_comments_or_observations = models.TextField(blank=True)

    # Section 2-B: Self-care and general oversight assessment-medications

    # Section 2-B.B
    requires_help_taking_medication = models.BooleanField(default=False)
    requires_help_with_self_administered_medication = models.BooleanField(default=False)
    requires_medication_administration = models.BooleanField(default=False)
    is_able_to_administer_without_assistance = models.BooleanField(default=False)
    is_dialysis_patient = models.BooleanField(default=False)
    is_under_hospice_care = models.BooleanField(default=False)

    # Section 2-B.C
    section_2_b_additional_comments = models.TextField(blank=True)

    # Medical Examination Info
    signature_on_file = models.BooleanField(default=False)
    examiner_name = models.CharField(max_length=255, blank=True)
    examiner_signature = models.ImageField(
        blank=True, null=True, upload_to=random_name_in("residents/examiner-signatures")
    )
    examiner_medical_license_number = models.CharField(max_length=255, blank=True)
    examiner_address = models.CharField(max_length=255, blank=True)
    examiner_phone = UsPhoneNumberField(blank=True)
    examiner_title = models.CharField(max_length=255, choices=ExaminerTitle, blank=True)
    examination_date = models.DateField(_("1823 Exam Due"), blank=True, null=True)

    # Section 3: Services offered or arranged by the facility for the resident
    gaurdian_or_recipient_name = models.CharField(max_length=255, blank=True)
    gaurdian_or_recipient_signature = models.ImageField(
        blank=True,
        null=True,
        upload_to=random_name_in("residents/gaurdian-or-recipient-signatures"),
    )
    administrator_or_designee_name = models.CharField(max_length=255, blank=True)
    administrator_or_designee_signature = models.ImageField(
        blank=True,
        null=True,
        upload_to=random_name_in("residents/administrator-or-designee-signatures"),
    )

    tracker = FieldTracker(
        fields=["examiner_signature", "long_term_care_provider", "date_of_discharge"]
    )

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        born = self.date_of_birth
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    @property
    def examination_interval(self):
        if not self.is_active:
            return None
        if self.examiner_signature or self.signature_on_file:
            return 12 if self.has_assistive_care_services else 36
        else:
            return 1

    @property
    def examination_due_date(self):
        interval = self.examination_interval
        if not interval:
            return ""
        if interval == 1:
            return (
                (self.date_of_admission + relativedelta(months=interval))
                if self.date_of_admission
                else ""
            )
        else:
            return (
                (self.examination_date + relativedelta(months=interval))
                if self.examination_date
                else ""
            )

    def __str__(self):
        return "{} {}".format(self.first_name, self.last_name)

    def __repr__(self):
        return "<Resident: {}>".format(self.pk)

    def save(self, *args, **kwargs):
        if self.tracker.has_changed("examiner_signature"):
            if self.examiner_signature:
                self.examiner_sign()
            else:
                self.examiner_unsign()
            if self.pk:
                self.archive_1823()

        return super(Resident, self).save(*args, **kwargs)

    def archive_1823(self):
        resident = Resident.objects.get(pk=self.pk)
        if resident.examiner_signature:
            context = {
                "resident": resident,
                "resident_medication_numbers": list(range(1, 13))[resident.medications.count() :],
                "resident_services_offered_numbers": list(range(1, 16))[
                    resident.services_offered.count() :
                ],
            }
            with TemporaryFile() as f:
                generate_pdf("residents/1823.pdf.html", f, context)
                archive = Archived1823(resident=resident, date_signed=resident.examination_date)
                archive.data_archived.save("Archive.pdf", File(f), save=True)

    def examiner_sign(self):
        self.has_completed_1823_on_file = True
        self.form_1823_completed_date = self.examination_date

    def examiner_unsign(self):
        self.has_completed_1823_on_file = False
        self.form_1823_completed_date = None

    @property
    def full_name(self):
        return "{} {}".format(self.first_name, self.last_name)


class MedicationFile(TimeStampedModel):
    resident = models.ForeignKey(
        Resident, related_name="medication_files", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    pdf_file = models.FileField(
        upload_to=random_name_in("residents/medications_files"), blank=True, null=True
    )


class ResidentBedHold(models.Model):
    resident = models.ForeignKey("Resident", related_name="bed_holds", on_delete=models.CASCADE)
    date_out = models.DateField()
    date_in = models.DateField(blank=True, null=True)
    sent_to = models.CharField(max_length=255, null=True, blank=True)
    notes = models.CharField(max_length=255, null=True, blank=True)

    @property
    def facility(self):
        return self.resident.facility

    class Meta:
        unique_together = ("resident", "date_out")

    def __str__(self):
        return "Bed hold for {} #{} {} - {}".format(
            self.resident, self.resident.id, self.date_out, self.date_in or "tbd"
        )


class ResidentMedication(models.Model):
    resident = models.ForeignKey("Resident", related_name="medications", on_delete=models.CASCADE)
    medication = models.CharField(max_length=100)
    dosage = models.CharField(max_length=100)
    directions_for_use = models.CharField(max_length=100)
    route = models.CharField(max_length=100)


class ServiceOffered(models.Model):
    resident = models.ForeignKey(
        "Resident", related_name="services_offered", on_delete=models.CASCADE
    )
    need_identified = models.CharField(max_length=100)
    service_needed = models.CharField(max_length=100)
    frequency_and_duration = models.CharField(max_length=100)
    service_provider_name = models.CharField(max_length=100)
    date_service_began = models.DateField()


class Archived1823(models.Model):
    date_signed = models.DateField()
    date_archived = models.DateField(auto_now_add=True)
    data_archived = models.FileField(upload_to=random_name_in("residents/archived1823s"))
    resident = models.ForeignKey("residents.Resident", on_delete=models.CASCADE)

    class Meta:
        ordering = ["-date_signed", "-id"]

    def __str__(self):
        return "1823 for {} signed on {}; Archived {}".format(
            self.resident, self.date_signed, self.date_archived
        )


class IlsFile(TimeStampedModel):
    generated_file = models.FileField(upload_to=random_name_in("residents/ils_file"))
    uploaded = models.BooleanField(default=False)

    def __str__(self):
        return "ILS file %i - Created at %s" % (
            self.id,
            self.created.strftime("%m/%d/%Y"),
        )


class Provider(TimeStampedModel):
    name = models.CharField(_("LTC Provider name"), max_length=255, unique=True)
    position = models.CharField(_("LTC provider position"), max_length=255, blank=True, null=True)
    contact = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"


class ProviderEmail(TimeStampedModel):
    email = models.EmailField()
    provider = models.ForeignKey("Provider", on_delete=models.CASCADE)


class ProviderFile(TimeStampedModel):
    from apps.residents.utils import provider_file_path

    file = models.FileField(upload_to=provider_file_path)
    provider = models.ForeignKey("Provider", on_delete=models.CASCADE)
