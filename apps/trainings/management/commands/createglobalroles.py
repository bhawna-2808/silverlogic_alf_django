from functools import partial

from django.core.management.base import BaseCommand

from ...models import (
    GlobalRequirement,
    Position,
    Responsibility,
    ResponsibilityEducationRequirement,
    Task,
    TaskType,
    TaskTypeEducationCredit,
    continuing_education_type_enum,
)


class Command(BaseCommand):
    help = "Creates the global responsibilities, task types, and positions"

    def handle(self, *args, **options):
        # Responsibilities
        def r(name, question=None):
            responsibility, _ = Responsibility.objects.get_or_create(name=name, facility=None)
            if question:
                responsibility.question = question
            responsibility.save()
            return responsibility

        r_home_health_aide = r("Home Health Aide")
        r_nursing_assist = r("Certified Nursing Assist Certificate")
        r_nursing_license = r("Nursing License")
        r_extended_congregate_care = r("Extended Congregate Care")
        r_limited_mental_health = r("Limited Mental Health")
        r_alz = r(
            "Provides Special Care for Persons with Alzheimer's",
            "Will this staff person be caring for Alzheimer's residents?",
        )
        r_admin = r("Administrator")
        r_food_service_mgr = r("Food Service Manager")
        r_food = r("Comes in Contact with Food", "Will this staff person be handling food?")
        r_cpr = r("CPR", "Will this staff person be required to have CPR?")
        r_first_aid = r("First Aid", "Will this staff person be required to have First Aid?")
        r_direct_care = r("Direct Care", "Do your administrators / managers provide direct care?")
        r_assist_self_med = r(
            "Assist with Self Administered Medication",
            "Will this staff person be handling medications?",
        )
        r_background = r("Background")
        r_food_handling = r("Food Handling")
        r_application = r("Application")
        r_tb_test = r("TB Test")
        r_elopement = r("Elopement")
        r_free_communicable = r("Free of Communicable Disease")
        r_job_description = r("Job Description")
        r_aids = r("AIDS/HIV")
        r_cna_license_renewal = r(
            "CNA License Renewal Reminder",
            "Do you want biannual reminders for CNA license renewal?",
        )

        # Positions
        def p(name, *responsibilities, **kwargs):
            position, _ = Position.objects.get_or_create(name=name, facility=None)
            position.responsibilities = [r.pk for r in responsibilities]
            position.description = kwargs.pop("description", None)
            position.save()
            return position

        p("Nurse", r_nursing_license, r_direct_care)
        p("Administrator", r_admin)
        p("Home Health Aide", r_home_health_aide)
        p_nursing_assistant = p("Nursing Assistant", r_nursing_assist)
        r_cna_license_renewal.question_position_restriction = p_nursing_assistant
        r_cna_license_renewal.save()
        p("Extended Congregate Care Supervisor", r_extended_congregate_care)
        p("Food Service Manager", r_food_service_mgr)
        p("Direct Care", r_direct_care)
        p(
            "Manager",
            r_admin,
            description=(
                '"Manager" means an individual who is authorized to perform the '
                "same functions of the administrator, and is responsible for the "
                "operation and maintenance of an assisted living facility while "
                "under the supervision of the administrator of that facility."
            ),
        )

        p(
            "Dietary",
            r_background,
            r_food_handling,
            r_application,
            r_tb_test,
            r_elopement,
            r_free_communicable,
            r_job_description,
            r_aids,
        )
        p(
            "Maintenance",
            r_background,
            r_application,
            r_tb_test,
            r_elopement,
            r_free_communicable,
            r_job_description,
            r_aids,
        )
        p(
            "Laundry Staff",
            r_background,
            r_application,
            r_tb_test,
            r_elopement,
            r_free_communicable,
            r_job_description,
            r_aids,
        )
        p(
            "House Keeping",
            r_background,
            r_application,
            r_tb_test,
            r_elopement,
            r_free_communicable,
            r_job_description,
            r_aids,
        )

        # Task Types
        def t(
            name,
            is_training=True,
            is_one_off=False,
            required_within=0,
            validity_period=0,
            required_for=[],
            prerequisites=[],
            supersedes=[],
        ):

            task_type, _ = TaskType.objects.get_or_create(name=name, facility=None)

            task_type.is_training = is_training
            task_type.is_one_off = is_one_off
            task_type.required_within = required_within
            task_type.validity_period = validity_period

            task_type.required_for.set(required_for)
            task_type.prerequisites.set(prerequisites)
            task_type.supersedes.set(supersedes)
            task_type.save()
            return task_type

        t_ahca_background_check_roster = t(
            "Added to AHCA Facilities Background Check Roster",
            is_training=False,
            is_one_off=True,
        )
        GlobalRequirement.objects.get_or_create(task_type=t_ahca_background_check_roster)
        t(
            "CNA License Renewal",
            is_training=False,
            validity_period="730 days",
            required_for=[r_cna_license_renewal],
        )

        direct_care_task_types = []

        def tdc(*args, **kwargs):
            _tdc = partial(t, is_training=False, is_one_off=True)
            task_type = _tdc(*args, **kwargs)
            task_type.required_for.add(r_direct_care)
            direct_care_task_types.append(task_type)
            return task_type

        tdc("Employment Application on File")
        tdc("Employement Application has 2 references listed")
        tdc("Employement Application state Date of Hire")
        t_provide_assistance = tdc(
            "3Hrs Resident behavior and needs and Providing assistance with "
            + "the activities of daily living"
        )
        t_infection_control = tdc(
            "Infection Control", required_for=[r_home_health_aide, r_nursing_assist]
        )
        tdc("Job Description")
        tdc(
            "Level 2 Background Screening",
            is_one_off=False,
            validity_period="1825 days",  # 5 years
        )
        tdc(
            "Negative Tuberculosis",
            is_one_off=True,
            validity_period="365 days",
            is_training=True,
        )
        tdc(
            "Free from Signs or Symptoms of Communicable Disease",
            required_within="30 days",
        )
        tdc(
            "First Aid",
            is_training=True,
            validity_period="730 days",
            required_for=[r_first_aid],
        )
        tdc("CPR", is_training=True, validity_period="730 days", required_for=[r_cpr])
        tdc("Facility Emergency Procedures", required_within="30 days")
        tdc(
            "1Hr Resident rights in an Assisted Living Facility and Recognizing "
            + "and Reporting Resident Abuse, Neglect, and Exploitation",
            required_within="30 days",
            is_training=True,
        )
        tdc(
            "Safe Food Handling Practices",
            required_within="30 days",
            required_for=[r_food],
            is_training=True,
        )
        tdc("Elopement Response Policies and Procedures", required_within="30 days")
        tdc(
            "Reporting Major and Averse Incidents",
            required_within="30 days",
            is_training=True,
        )
        tdc("HIV/AIDS", required_within="30 days", is_training=True)
        tdc(
            "Facility's Policies and Procedures Regarding DNROs",
            required_within="30 days",
            is_training=True,
        )

        # Need to apply supersedes farther down
        t_home_health_aide_cert = tdc(
            "Home Health Aide Certification",
            supersedes=[t_infection_control, t_provide_assistance],
        )
        t_certified_nursing_assist_cert = tdc(
            "Certified Nursing Assist Certificate",
            supersedes=[
                t_home_health_aide_cert,
                t_infection_control,
                t_provide_assistance,
            ],
        )
        t_home_health_aide_cert.supersedes.add(t_certified_nursing_assist_cert)

        t_core = t("Core Training", validity_period="730 days", required_for=[r_admin])
        t_extended_congregate_care = t(
            "Extended Congregate Core Training",
            is_one_off=True,
            required_within="12 weeks",
            required_for=[r_extended_congregate_care],
            prerequisites=[t_core],
        )
        t_limited_mental_health = t(
            "Limited Mental Health Training",
            is_one_off=True,
            required_within="24 weeks",
            required_for=[r_limited_mental_health],
        )
        t_nursing_license = t(
            "Nursing License",
            is_training=False,
            is_one_off=True,
            required_for=[r_nursing_license],
            supersedes=[],
        )
        t_alz_1 = t(
            "Alzheimer's Training 1",
            is_one_off=True,
            required_within="12 weeks",
            required_for=[r_alz],
        )
        t_alz_2 = t(
            "Alzheimer's Training 2",
            is_one_off=True,
            required_within="36 weeks",
            required_for=[r_alz],
            prerequisites=[t_alz_1],
        )
        t(
            "Assist with Self Administered Medication Training",
            is_one_off=True,
            validity_period="365 days",
            required_for=[r_assist_self_med],
        )
        t_food_service_mgr_cert = t(
            "Food Service Manager Certification", validity_period="1825 days"
        )

        t_nursing_license.supersedes = direct_care_task_types
        t_nursing_license.save()

        # Responsiblity Educations
        ResponsibilityEducationRequirement.objects.get_or_create(
            responsibility=r_extended_congregate_care,
            hours=4,
            type=continuing_education_type_enum.any,
            timeperiod="730 days",
            interval_base=t_extended_congregate_care,
        )
        ResponsibilityEducationRequirement.objects.get_or_create(
            responsibility=r_admin,
            hours=12,
            type=continuing_education_type_enum.admin,
            timeperiod="730 days",
            interval_base=t_core,
        )
        ResponsibilityEducationRequirement.objects.get_or_create(
            responsibility=r_alz,
            hours=4,
            type=continuing_education_type_enum.alzheimers,
            timeperiod="365 days",
            interval_base=t_alz_2,
        )
        ResponsibilityEducationRequirement.objects.get_or_create(
            responsibility=r_food_service_mgr,
            hours=2,
            type=continuing_education_type_enum.any,
            timeperiod="365 days",
            interval_base=t_food_service_mgr_cert,
        )
        ResponsibilityEducationRequirement.objects.get_or_create(
            responsibility=r_limited_mental_health,
            hours=6,
            type=continuing_education_type_enum.any,
            timeperiod="365 days",  # TODO(Ryan): Is this right?
            interval_base=t_limited_mental_health,
        )

        t_core_training_edu = t(
            "Core Training Continuing Education",
            validity_period="730 days",
            prerequisites=[t_core],
        )
        TaskTypeEducationCredit.objects.get_or_create(
            type=continuing_education_type_enum.admin, tasktype=t_core_training_edu
        )

        t_limited_mental_health_edu = t(
            "Limited Mental Health Continuing Education",
            validity_period="730 days",
            prerequisites=[t_limited_mental_health],
        )
        TaskTypeEducationCredit.objects.get_or_create(
            type=continuing_education_type_enum.any,
            tasktype=t_limited_mental_health_edu,
        )

        t_assist_with_self_medicine_edu = t(
            "Assist with Self Administered Medication Training Continuing Education",
            validity_period="365 days",
        )
        TaskTypeEducationCredit.objects.get_or_create(
            type=continuing_education_type_enum.any,
            tasktype=t_assist_with_self_medicine_edu,
        )

        # Fix task due dates
        for task in Task.objects.all():
            task.recompute_due_date()
