from datetime import date, datetime, timedelta

from django.contrib.auth.models import User
from django.utils import timezone

import factory

from apps.facilities.models import FacilityUser, UserInvite
from apps.subscriptions.models import BillingInterval
from apps.trainings.models import TaskHistoryStatus, TaskStatus, continuing_education_type_enum


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: "user{}".format(n))
    password = factory.PostGenerationMethodCall("set_password", "admin")
    email = factory.Faker("email")

    class Meta:
        model = User
        django_get_or_create = ("username",)


class BusinessAgreementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "facilities.BusinessAgreement"
        django_get_or_create = ("facility",)

    signed_by = factory.SubFactory(
        "tests.factories.FacilityUserFactory",
        facility=factory.SelfAttribute("..facility"),
        user__username=factory.Faker("name"),
    )


class FacilityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "trainings.Facility"
        django_get_or_create = ("name",)

    name = "facility 1"
    capacity = 500
    businessagreement = factory.RelatedFactory(BusinessAgreementFactory, "facility")


class EmployeeFactory(factory.django.DjangoModelFactory):
    first_name = factory.Sequence(lambda n: "first{}".format(n))
    last_name = factory.Sequence(lambda n: "last{}".format(n))
    facility = factory.SubFactory("tests.factories.FacilityFactory")
    user = factory.SubFactory("tests.factories.UserFactory")
    date_of_hire = date(2014, 1, 1)
    ssn = "665-12-4567"
    phone_number = "(905) 123-4567"
    date_of_birth = date(1995, 2, 27)  # The bestest ever.
    email = "test@tester.com"

    class Meta:
        model = "trainings.Employee"

    @factory.post_generation
    def positions(obj, create, extracted, **kwargs):
        if create and extracted:
            obj.positions.set(extracted)

    @factory.post_generation
    def other_responsibilities(obj, create, extracted, **kwargs):
        if create and extracted:
            obj.other_responsibilities.set(extracted)


class FacilityUserFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory("tests.factories.UserFactory")
    facility = factory.SubFactory("tests.factories.FacilityFactory")
    role = FacilityUser.Role.account_admin

    class Meta:
        model = "facilities.FacilityUser"


class UserInviteFactory(factory.django.DjangoModelFactory):
    facility = factory.SubFactory("tests.factories.FacilityFactory")
    email = factory.Faker("email")
    role = UserInvite.Role.manager
    invited_by = factory.SubFactory("tests.factories.UserFactory")

    class Meta:
        model = "facilities.UserInvite"


class UserResidentAccessFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory("tests.factories.FacilityUserFactory")
    resident = factory.SubFactory("tests.factories.ResidentFactory")

    class Meta:
        model = "facilities.UserResidentAccess"


class UserInviteResidentAccessFactory(factory.django.DjangoModelFactory):
    invite = factory.SubFactory("tests.factories.UserInviteFactory")
    resident = factory.SubFactory("tests.factories.ResidentFactory")

    class Meta:
        model = "facilities.UserInviteResidentAccess"


class TaskTypeFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "task type {}".format(n))
    required_within = "3 days"
    validity_period = "1 week"
    is_one_off = False

    class Meta:
        model = "trainings.TaskType"

    @factory.post_generation
    def required_for(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.required_for.set(extracted)

    @factory.post_generation
    def prerequisites(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.prerequisites.set(extracted)

    @factory.post_generation
    def supersedes(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.supersedes.set(extracted)


class CustomTaskTypeFactory(TaskTypeFactory):
    facility = factory.SubFactory("tests.factories.FacilityFactory")

    class Meta:
        model = "trainings.CustomTaskType"


class CourseFactory(factory.django.DjangoModelFactory):
    task_type = factory.SubFactory("tests.factories.TaskTypeFactory")
    name = factory.Sequence(lambda n: "course {}".format(n))
    description = factory.Sequence(lambda n: "description {}".format(n))
    objective = factory.Sequence(lambda n: "objective {}".format(n))
    duration = 3
    minimum_score = 3

    class Meta:
        model = "trainings.Course"


class EmployeeCourseFactory(factory.django.DjangoModelFactory):
    course = factory.SubFactory("tests.factories.CourseFactory")
    employee = factory.SubFactory("tests.factories.EmployeeFactory")
    start_date = "2019-04-01"
    completed_date = "2019-04-01"

    class Meta:
        model = "trainings.EmployeeCourse"


class CourseItemFactory(factory.django.DjangoModelFactory):
    course = factory.SubFactory("tests.factories.CourseFactory")
    title = factory.Sequence(lambda n: "title {}".format(n))

    class Meta:
        model = "trainings.CourseItem"


class CourseItemTextFactory(factory.django.DjangoModelFactory):
    item = factory.SubFactory("tests.factories.CourseItemFactory")
    question = factory.Sequence(lambda n: "question {}".format(n))
    answer = factory.Sequence(lambda n: "answer {}".format(n))

    class Meta:
        model = "trainings.CourseItemText"


class CourseItemBooleanFactory(factory.django.DjangoModelFactory):
    item = factory.SubFactory("tests.factories.CourseItemFactory")
    question = factory.Sequence(lambda n: "question {}".format(n))

    class Meta:
        model = "trainings.CourseItemBoolean"


class MultiChoiceOptionFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: "option {}".format(n))

    class Meta:
        model = "trainings.MultiChoiceOption"


class CourseItemMultiChoiceFactory(factory.django.DjangoModelFactory):
    item = factory.SubFactory("tests.factories.CourseItemFactory")
    question = factory.Sequence(lambda n: "question {}".format(n))

    class Meta:
        model = "trainings.CourseItemMultiChoice"


class CourseItemVideoFactory(factory.django.DjangoModelFactory):
    item = factory.SubFactory("tests.factories.CourseItemFactory")
    link = factory.Sequence(lambda n: "link {}".format(n))

    class Meta:
        model = "trainings.CourseItemVideo"


class CourseItemLetterSizeImageFactory(factory.django.DjangoModelFactory):
    item = factory.SubFactory("tests.factories.CourseItemFactory")

    class Meta:
        model = "trainings.CourseItemLetterSizeImage"


class EmployeeCourseItemFactory(factory.django.DjangoModelFactory):
    course_item = factory.SubFactory("tests.factories.CourseItemFactory")
    employee = factory.SubFactory("tests.factories.EmployeeFactory")
    started_at = timezone.now()

    class Meta:
        model = "trainings.EmployeeCourseItem"


class PositionFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "position {}".format(n))
    responsibilities = []

    class Meta:
        model = "trainings.Position"

    @factory.post_generation
    def responsibilities(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.responsibilities.set(extracted)


class TaskFactory(factory.django.DjangoModelFactory):
    employee = factory.SubFactory("tests.factories.EmployeeFactory")
    type = factory.SubFactory("tests.factories.TaskTypeFactory")
    due_date = timezone.now().date()
    status = TaskStatus.open

    class Meta:
        model = "trainings.Task"

    @factory.post_generation
    def overdue(self, create, extracted, **kwargs):
        if extracted:
            self.due_date = date.today() - timedelta(days=1)


class TrainingEventFactory(factory.django.DjangoModelFactory):
    training_for = factory.SubFactory("tests.factories.TaskTypeFactory")
    start_time = timezone.make_aware(datetime(2014, 1, 1, 11, 30), timezone.get_current_timezone())
    end_time = timezone.make_aware(datetime(2014, 1, 1, 14, 45), timezone.get_current_timezone())
    location = "The J Wing"
    facility = factory.SubFactory("tests.factories.FacilityFactory")

    class Meta:
        model = "trainings.TrainingEvent"

    @factory.post_generation
    def attendees(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.attendees.set(extracted)


class ResponsibilityFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "responsibility {}".format(n))
    facility = factory.SubFactory("tests.factories.FacilityFactory")

    class Meta:
        model = "trainings.Responsibility"


class TaskHistoryFactory(factory.django.DjangoModelFactory):
    employee = factory.SubFactory("tests.factories.EmployeeFactory")
    type = factory.SubFactory("tests.factories.TaskTypeFactory")
    completion_date = date.today()
    expiration_date = date.today() + timedelta(days=700)
    status = TaskHistoryStatus.completed
    credit_hours = 0

    class Meta:
        model = "trainings.TaskHistory"


class TaskHistoryCertificateFactory(factory.django.DjangoModelFactory):
    task_history = factory.SubFactory("tests.factories.TaskHistoryFactory")

    class Meta:
        model = "trainings.TaskHistoryCertificate"


class ResponsibilityEducationRequirementFactory(factory.django.DjangoModelFactory):
    hours = 40
    interval_base = factory.SubFactory("tests.factories.TaskTypeFactory")
    timeperiod = timedelta(days=700)
    type = continuing_education_type_enum.any
    responsibility = factory.SubFactory("tests.factories.ResponsibilityFactory")

    class Meta:
        model = "trainings.ResponsibilityEducationRequirement"


class TaskTypeEducationCreditFactory(factory.django.DjangoModelFactory):
    type = continuing_education_type_enum.any
    tasktype = factory.SubFactory("tests.factories.TaskTypeFactory")

    class Meta:
        model = "trainings.TaskTypeEducationCredit"


class FacilityQuestionFactory(factory.django.DjangoModelFactory):
    question = "Does this facility smell what The Rock is cooking?"
    is_license = False
    description = "The Rock is cooking something nasty."

    class Meta:
        model = "trainings.FacilityQuestion"


class FacilityQuestionRuleFactory(factory.django.DjangoModelFactory):
    facility_question = factory.SubFactory("tests.factories.FacilityQuestionFactory")
    position = factory.SubFactory("tests.factories.PositionFactory")
    responsibility = factory.SubFactory("tests.factories.ResponsibilityFactory")

    class Meta:
        model = "trainings.FacilityQuestionRule"


class AntirequisiteFactory(factory.django.DjangoModelFactory):
    task_type = factory.SubFactory("tests.factories.TaskTypeFactory")
    antirequisite_of = factory.SubFactory("tests.factories.TaskTypeFactory")
    valid_after_hire_date = date(2014, 12, 25)

    class Meta:
        model = "trainings.Antirequisite"


class GlobalRequirementFactory(factory.django.DjangoModelFactory):
    task_type = factory.SubFactory("tests.factories.TaskTypeFactory")

    class Meta:
        model = "trainings.GlobalRequirement"


class ResidentFactory(factory.django.DjangoModelFactory):
    facility = factory.SubFactory("tests.factories.FacilityFactory")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    class Meta:
        model = "residents.Resident"


class ResidentBedHoldFactory(factory.django.DjangoModelFactory):
    resident = factory.SubFactory("tests.factories.ResidentFactory")
    date_out = factory.Faker("date")
    date_in = factory.Faker("date")
    sent_to = factory.Faker("word")
    notes = factory.Faker("word")

    class Meta:
        model = "residents.ResidentBedHold"


class ResidentMedicationFactory(factory.django.DjangoModelFactory):
    resident = factory.SubFactory("tests.factories.ResidentFactory")
    medication = factory.Faker("word")
    dosage = factory.Faker("word")
    directions_for_use = factory.Faker("word")
    route = factory.Faker("word")

    class Meta:
        model = "residents.ResidentMedication"


class ResidentMedicationFileFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    pdf_file = factory.django.FileField(filename="my.pdf")

    class Meta:
        model = "residents.MedicationFile"


class ServiceOfferedFactory(factory.django.DjangoModelFactory):
    resident = factory.SubFactory("tests.factories.ResidentFactory")
    need_identified = factory.Faker("sentence")
    service_needed = factory.Faker("sentence")
    frequency_and_duration = factory.Faker("word")
    service_provider_name = factory.Faker("name")
    date_service_began = factory.Faker("date")

    class Meta:
        model = "residents.ServiceOffered"


class Archived1823Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = "residents.Archived1823"


class IlsFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "residents.IlsFile"


class PlanFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    module = factory.Iterator(["staff", "resident"])

    class Meta:
        model = "subscriptions.Plan"


class BillingIntervalFactory(factory.django.DjangoModelFactory):
    stripe_id = ""
    plan = factory.SubFactory("tests.factories.PlanFactory")
    amount = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    interval = BillingInterval.Interval.month
    interval_count = 1

    class Meta:
        model = "subscriptions.BillingInterval"


class SubscriptionFactory(factory.django.DjangoModelFactory):
    stripe_id = ""
    facility = factory.SubFactory("tests.factories.FacilityFactory")
    billing_interval = factory.SubFactory("tests.factories.BillingIntervalFactory")
    current_period_start = factory.Faker("date_time", tzinfo=timezone.get_current_timezone())
    current_period_end = factory.Faker("date_time", tzinfo=timezone.get_current_timezone())

    class Meta:
        model = "subscriptions.Subscription"


class SponsorFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")
    amount_paid = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    # facility = factory.SubFactory('tests.factories.FacilityFactory')

    class Meta:
        model = "subscriptions.Sponsor"


class SponsorshipFactory(factory.django.DjangoModelFactory):
    facility = factory.SubFactory("tests.factories.FacilityFactory")
    sponsor = factory.SubFactory("tests.factories.SponsorFactory")
    start_date = factory.Faker("date")

    class Meta:
        model = "subscriptions.Sponsorship"


class FacilityPaymentMethodFactory(factory.django.DjangoModelFactory):
    stripe_token = "asdf1231"
    facility = factory.SubFactory("tests.factories.FacilityFactory")

    class Meta:
        model = "subscriptions.FacilityPaymentMethod"


class DirectoryFacilityFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("company")
    license_number = "1234"
    oss_beds = factory.Faker("pyint")
    private_beds = factory.Faker("pyint")

    class Meta:
        model = "alfdirectory.Facility"


class ExaminerFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(
        "tests.factories.UserFactory",
        username=factory.Sequence(lambda n: "examiner{}".format(n)),
    )
    medical_license_number = "12345"

    class Meta:
        model = "examiners.Examiner"


class TrainingsUserFactory(EmployeeFactory):
    user = factory.SubFactory(
        "tests.factories.UserFactory",
        username=factory.Sequence(lambda n: "app user{}".format(n)),
    )


class ResidentAccessFactory(factory.django.DjangoModelFactory):
    examiner = factory.SubFactory("tests.factories.ExaminerFactory")
    resident = factory.SubFactory("tests.factories.ResidentFactory")

    class Meta:
        model = "examiners.ResidentAccess"


class ExaminationRequestFactory(factory.django.DjangoModelFactory):
    examiner = factory.SubFactory("tests.factories.ExaminerFactory")
    resident = factory.SubFactory("tests.factories.ResidentFactory")

    class Meta:
        model = "examiners.ExaminationRequest"


class TutorialVideoFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("word")

    class Meta:
        model = "tutorials.TutorialVideo"


def admin_user():
    facility_user = FacilityUserFactory(user=UserFactory(username="admin"))
    return facility_user.user


def login(f):
    def login_(self):
        user = admin_user()
        self.client.force_authenticate(user=user)
        self.logged_in_as = user
        self.logged_in_facility = FacilityUser.objects.get(user=user).facility
        f(self)

    return login_


def logout(f):
    def logout_(self):
        self.logged_in_as = None
        self.client.force_authenticate()
        f(self)

    return logout_
