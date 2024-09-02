import uuid
from datetime import datetime, timedelta
from functools import reduce

from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.timezone import localtime

from autoslug import AutoSlugField
from localflavor.us.models import USSocialSecurityNumberField, USStateField, USZipCodeField
from model_utils import Choices, FieldTracker
from model_utils.models import TimeStampedModel

from apps.base.geocoder import get_geolocation_point
from apps.base.models import UsPhoneNumberField, random_name_in
from apps.utils.general import Enumeration
from apps.utils.model_fields import ProperNameField

from .managers import EmployeeManager, TaskManager
from .utils_facility import have_sponsorships_started

BOOLEAN_INTS = (
    (1, "True"),
    (0, "False"),
    (-1, "Empty"),
)


class Facility(TimeStampedModel):
    name = models.TextField()
    directory_facility = models.ForeignKey(
        "alfdirectory.Facility", blank=True, null=True, on_delete=models.SET_NULL
    )
    questions = models.ManyToManyField("FacilityQuestion", blank=True)
    tax_id = models.CharField(max_length=255, blank=True, default="")

    # Location
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    address_city = models.CharField(max_length=255)
    state = USStateField(
        null=True, help_text="DEPRECATED FIELD. USE state_facility INSTEAD"
    )  # legacy so it doesn't start with address_
    state_facility = models.ForeignKey(
        "alfdirectory.State",
        null=True,
        related_name="trainings_facilities",
        on_delete=models.SET_NULL,
    )
    address_zipcode = USZipCodeField()
    address_county = models.CharField(max_length=255, blank=True)
    point = gis_models.PointField(blank=True, null=True)

    # Contact
    primary_administrator_name = models.CharField(max_length=255)
    contact_phone = UsPhoneNumberField()
    contact_fax = UsPhoneNumberField(default="", blank=True)
    contact_email = models.EmailField()

    # Modules
    is_staff_module_enabled = models.BooleanField(
        default=True, blank=True, help_text="This just hides the module in the FE"
    )
    is_resident_module_enabled = models.BooleanField(default=True)
    is_lms_module_enabled = models.BooleanField(default=have_sponsorships_started)
    fcc_signup = models.BooleanField(default=False)

    # Sponsorship
    opted_in_sponsorship_date = models.DateField(null=True, blank=True)
    sponsored_access = models.BooleanField(default=have_sponsorships_started)

    # Residents
    capacity = models.PositiveIntegerField(default=0)

    # Ebook
    bought_ebook = models.BooleanField(default=False)

    npi = models.CharField(max_length=10, blank=True)

    admin_signature = models.ImageField(
        null=True,
        blank=True,
        upload_to=random_name_in("residents/administrator-or-designee-signatures"),
    )

    class Meta:
        verbose_name_plural = "facilities"

    def __init__(self, *args, **kwargs):
        super(Facility, self).__init__(*args, **kwargs)
        self.initial_capacity = self.capacity

    def __str__(self):
        return self.name

    @property
    def first_aid_cpr(self):
        return self.questions.filter(slug=slugify("first aid and cpr")).exists()

    @property
    def alzheimer(self):
        return self.questions.filter(
            Q(slug=slugify("special care for alzheimers"))
            | Q(slug=slugify("secured areas for alzheimers"))
        ).exists()

    @property
    def address(self):
        """address condensed to 1 line."""
        s = ""
        s += self.address_line1 + ", "
        if self.address_line2:
            s += self.address_line2 + ", "
        s += self.address_city + ", "
        s += (self.state or "") + " "
        s += self.address_zipcode
        return s

    @property
    def geolocation(self):
        if self.point:
            return self.point

        point = get_geolocation_point(self.address)
        if not point:
            point = get_geolocation_point(self.address_zipcode)

        if point:
            # Avoid post save signal
            Facility.objects.filter(id=self.id).update(point=point)
        return point

    @property
    def licenses(self):
        return self.questions.filter(is_license=True)


class Responsibility(TimeStampedModel):
    facility = models.ForeignKey(
        Facility, blank=True, null=True, default=None, on_delete=models.CASCADE
    )
    name = models.TextField()
    question = models.TextField(blank=True)
    question_position_restriction = models.ForeignKey(
        "Position", blank=True, null=True, on_delete=models.CASCADE
    )

    class Meta:
        verbose_name_plural = "responsibilities"
        ordering = ("name",)
        unique_together = (
            "name",
            "facility",
        )

    def __str__(self):
        return self.name


continuing_education_type_enum = Enumeration(
    (1, "any", "Any"),
    (2, "admin", "Admin"),
    (3, "alzheimers", "Alzheimers"),
)


class ResponsibilityEducationRequirement(TimeStampedModel):
    hours = models.PositiveSmallIntegerField(default=0)
    interval_base = models.ForeignKey("TaskType", on_delete=models.CASCADE)
    timeperiod = models.DurationField()
    type = models.PositiveSmallIntegerField(choices=continuing_education_type_enum)
    responsibility = models.ForeignKey(
        Responsibility, related_name="education_requirements", on_delete=models.CASCADE
    )
    start_over = models.BooleanField(default=False)

    def __str__(self):
        return "{} {} {} {} {}".format(
            self.hours,
            self.interval_base,
            self.timeperiod,
            self.type,
            self.responsibility,
        )


class Position(TimeStampedModel):
    class Meta:
        ordering = ("name",)

    name = models.TextField(unique=True)
    description = models.TextField(blank=True, null=True)
    responsibilities = models.ManyToManyField(Responsibility, blank=True)
    group = models.ForeignKey("PositionGroup", null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


DeactivationReason = Enumeration(
    (1, "quit", "Quit"),
    (2, "fired", "Fired"),
)


class Employee(TimeStampedModel):
    first_name = ProperNameField()
    last_name = ProperNameField()
    email = models.EmailField(max_length=254, null=True, blank=True)
    picture = models.ImageField(
        blank=True, null=True, upload_to=random_name_in("employees/employee/pictures")
    )

    address = models.TextField(blank=True)
    address2 = models.TextField(blank=True)
    city = models.TextField(blank=True)
    state = USStateField(blank=True)
    zip_field = models.CharField(blank=True, max_length=50)
    invite_code = models.CharField(blank=True, max_length=10)

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    user = models.OneToOneField(
        User, blank=True, null=True, related_name="employee", on_delete=models.CASCADE
    )
    date_of_hire = models.DateField()
    positions = models.ManyToManyField(Position)
    other_responsibilities = models.ManyToManyField(Responsibility, blank=True)
    ssn = USSocialSecurityNumberField(blank=True)
    phone_number = UsPhoneNumberField(blank=True, max_length=50)
    job_description = models.TextField(blank=True)
    application_references = models.SmallIntegerField(default=0)
    date_of_birth = models.DateField(null=True, blank=True)

    is_reactivated = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    code_verified = models.BooleanField(default=False)
    receives_emails = models.BooleanField(default=False)

    deactivation_reason = models.PositiveSmallIntegerField(
        choices=DeactivationReason, default=None, blank=True, null=True
    )
    deactivation_date = models.DateField(blank=True, null=True)
    deactivation_note = models.TextField(blank=True)

    _orig_date_of_hire = None

    tracker = FieldTracker(fields=["is_active", "deactivation_date", "date_of_hire"])

    objects = EmployeeManager()

    def __init__(self, *args, **kwargs):
        super(Employee, self).__init__(*args, **kwargs)
        self._orig_date_of_hire = self.date_of_hire

    @property
    def full_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    def __str__(self):
        return self.full_name

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save(update_fields=["is_active"])

    def save(self, *args, **kwargs):
        if self._is_date_of_hire_changed():
            for task in self.trainings_task_set.all():
                task.recompute_due_date()
        super(Employee, self).save(*args, **kwargs)

    def _is_date_of_hire_changed(self):
        return self.date_of_hire != self._orig_date_of_hire

    def is_admin(self):
        return self.positions.filter(name="Administrator").exists()

    def set_invite_code(self):
        uid = uuid.uuid4()
        self.invite_code = uid.hex[:6].upper()

    def get_tasktypes_allowed_by_prerequisites(self):
        # put the ids of completed tasks in a map
        completed_tasks_map = {}
        completed_task_queryset = TaskHistory.objects.filter(
            employee_id=self.id, status=TaskHistoryStatus.completed
        )
        for completed_task in completed_task_queryset:
            completed_tasks_map[completed_task.type.id] = True

        # define function to filter a task list and a training list

        def check_prerequisites(tasktype):
            # if a task is not found in the completed task map then it fails
            # the prerequisite check
            for prereq in tasktype.prerequisites.all():
                if prereq.id == tasktype.id:
                    continue
                if not completed_tasks_map.get(prereq.id):
                    return False
            return True

        # users that are selecting a task to complete only see a filtered list
        # of tasks or trainings
        return list(filter(check_prerequisites, TaskType.objects.all()))

    def get_required_tasktypes(self):
        return TaskType.objects.filter(
            Q(facility=self.facility) | Q(facility=None),
            Q(required_for__in=self.other_responsibilities.all())
            | Q(globalrequirement__isnull=False),
        )


TaskStatus = Enumeration(
    (1, "open", "Open"),
    (2, "scheduled", "Scheduled"),
)

TaskHistoryStatus = Enumeration(
    (1, "incomplete", "Incomplete"),
    (2, "completed", "Completed"),
)


class TaskType(TimeStampedModel):
    name = models.TextField()
    is_training = models.BooleanField(default=False)
    is_one_off = models.BooleanField(default=False)
    hide_in_lms = models.BooleanField(default=False)

    min_capacity = models.PositiveIntegerField(
        default=0,
        help_text=(
            "Minimum required (inclusive) for Facility capacity for this Task to be required. "
            "Leave 0 if there is no minimum."
        ),
    )
    max_capacity = models.PositiveIntegerField(
        default=0,
        help_text=(
            "Maximum required (inclusive) for Facility capacity for this Task to be required. "
            "Leave 0 if there is no maximum."
        ),
    )

    required_within = models.DurationField(
        blank=True,
        default=timedelta(),
        help_text=(
            "How long after the employees hire date/required after "
            "task type should this task type be due?"
        ),
    )
    required_after_task_type = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        related_name="required_after_self",
        help_text=(
            "When filled out, modifies the required_within field to refer "
            "to when this task type is completed, instead of the "
            "employees hire date."
        ),
        on_delete=models.CASCADE,
    )

    validity_period = models.DurationField(blank=True, default=timedelta())
    required_for = models.ManyToManyField(Responsibility, blank=True)
    facility = models.ForeignKey(Facility, null=True, blank=True, on_delete=models.CASCADE)
    prerequisites = models.ManyToManyField("self", blank=True, symmetrical=False)
    supersedes = models.ManyToManyField(
        "self", blank=True, symmetrical=False, related_name="superseded_by"
    )
    rule = models.TextField(blank=True)
    image = models.ImageField(blank=True, null=True, upload_to=random_name_in("tasktype"))

    external_training_required = models.BooleanField(default=False)
    external_training_url = models.URLField(blank=True)

    def __init__(self, *args, **kwargs):
        super(TaskType, self).__init__(*args, **kwargs)
        self.initial_min_capacity = self.min_capacity
        self.initial_max_capacity = self.max_capacity

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(TaskType, self).save(*args, **kwargs)
        for task in self.task_set.all():
            task.save()

    def is_global_requirement(self):
        return hasattr(self, "globalrequirement")

    def is_continuing_education(self):
        return self.education_credits.all().exists()

    def check_capacity(self, employee):
        """Returns whether the task type should apply to the employee based on capacity"""
        if self.min_capacity == 0 and self.max_capacity == 0:
            return True

        capacity = employee.facility.capacity
        if capacity == 0:
            return False

        validated_min = self.min_capacity == 0 or self.min_capacity <= capacity
        validated_max = self.max_capacity == 0 or self.max_capacity >= capacity
        return validated_min and validated_max


class CustomTaskTypePrerequisite(TimeStampedModel):
    custom_task_type = models.ForeignKey(
        "CustomTaskType", related_name="prerequisites", on_delete=models.CASCADE
    )
    prerequisite = models.ForeignKey("TaskType", on_delete=models.CASCADE)


class CustomTaskTypeSupersede(TimeStampedModel):
    custom_task_type = models.ForeignKey(
        "CustomTaskType", related_name="supersedes", on_delete=models.CASCADE
    )
    supersede = models.ForeignKey("TaskType", on_delete=models.CASCADE)


class CustomTaskTypeRequiredFor(TimeStampedModel):
    custom_task_type = models.ForeignKey(
        "CustomTaskType", related_name="required_for", on_delete=models.CASCADE
    )
    required_for = models.ForeignKey(Responsibility, on_delete=models.CASCADE)


class CustomTaskType(TimeStampedModel):
    class Meta:
        unique_together = (
            "name",
            "facility",
        )

    name = models.TextField()
    description = models.TextField()
    is_training = models.BooleanField(default=False)
    is_one_off = models.BooleanField(default=False)
    required_within = models.DurationField(blank=True, default=timedelta())
    validity_period = models.DurationField(blank=True, default=timedelta())
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    rule = models.TextField(blank=True)
    is_request = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class TaskTypeEducationCredit(TimeStampedModel):
    type = models.PositiveSmallIntegerField(choices=continuing_education_type_enum)
    tasktype = models.ForeignKey(
        TaskType, related_name="education_credits", on_delete=models.CASCADE
    )
    facility = models.ForeignKey(Facility, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return "{} {}".format(self.type, self.tasktype)


class TaskBase(TimeStampedModel):
    class Meta:
        abstract = True

    employee = models.ForeignKey(
        Employee, related_name="%(app_label)s_%(class)s_set", on_delete=models.CASCADE
    )
    type = models.ForeignKey(TaskType, on_delete=models.CASCADE)
    antirequisite = models.ForeignKey(
        "Antirequisite", null=True, blank=True, on_delete=models.CASCADE
    )


class TaskHistory(TaskBase):
    completion_date = models.DateField(null=True)
    expiration_date = models.DateField(null=True)
    status = models.SmallIntegerField(choices=TaskHistoryStatus)
    credit_hours = models.FloatField(blank=True, default=0)

    def delete(self, *args, **kwargs):
        super(TaskHistory, self).delete(*args, **kwargs)

        related_task, _ = Task.objects.get_or_create(employee=self.employee, type=self.type)
        related_task.recompute_due_date()

        superseded_types = self.type.supersedes.all()
        superseded_one_off_types = superseded_types.filter(is_one_off=True)
        superseded_repeat_types = superseded_types.filter(is_one_off=False)

        superseded_tasks = Task.objects.filter(
            employee=self.employee, type__in=superseded_repeat_types
        )
        for task in superseded_tasks:
            task.recompute_due_date()

        for type in superseded_one_off_types:
            task = Task.objects.create(employee=self.employee, type=type)
            task.recompute_due_date()

        required_after_self_tasks = Task.objects.filter(
            employee=self.employee, type__in=self.type.required_after_self.all()
        )
        for task in required_after_self_tasks:
            task.recompute_due_date()


class TaskHistoryCertificate(TimeStampedModel):
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True)
    task_history = models.OneToOneField(
        TaskHistory, related_name="certificate", on_delete=models.CASCADE
    )

    def __str__(self):
        return "Certificate for task history {}".format(self.task_history)


class TaskHistoryCertificatePage(TimeStampedModel):
    certificate = models.ForeignKey(
        TaskHistoryCertificate, related_name="pages", on_delete=models.CASCADE
    )
    page = models.FileField(upload_to=random_name_in("certificates"))

    @property
    def isImage(self):
        return self.page.name[-3:] in ["jpg", "png"]

    def __str__(self):
        return "Page of {}".format(self.certificate)


class Task(TaskBase):
    due_date = models.DateField(blank=True, null=True)
    status = models.SmallIntegerField(choices=TaskStatus, default=TaskStatus.open)
    is_optional = models.BooleanField(
        default=False,
        help_text="This flag is used for when an employee starts a course"
        " that is not part of his responsibilities",
    )
    objects = TaskManager()

    class Meta:
        unique_together = (("employee", "type"),)

    def __str__(self):
        return self.type.name

    def save(self, *args, **kwargs):
        # We need this to play nice with the pre_save signal.
        kwargs["force_insert"] = False
        super(Task, self).save(*args, **kwargs)

    @property
    def scheduled_event(self):
        try:
            return self.training_events.earliest("start_time")
        except TrainingEvent.DoesNotExist:
            return None

    def complete(self, completion_date, credit_hours=0):
        if credit_hours and not self.type.is_continuing_education():
            credit_hours = 0
        self.type.refresh_from_db()
        th = TaskHistory.objects.create(
            employee=self.employee,
            type=self.type,
            status=TaskHistoryStatus.completed,
            completion_date=completion_date,
            expiration_date=completion_date + self.type.validity_period,
            credit_hours=credit_hours,
        )

        supersedes = Task.objects.filter(
            employee=self.employee, type__in=self.type.supersedes.all()
        )

        compare_date = (
            completion_date.date() if isinstance(completion_date, datetime) else completion_date
        )
        if compare_date < self.employee.date_of_hire:
            antirequisite = Antirequisite.objects.filter(
                antirequisite_of=self.type,
                valid_after_hire_date__lte=self.employee.date_of_hire,
            ).first()
        else:
            antirequisite = None

        if self.type.is_one_off:
            self.delete()
            for task in supersedes:
                task.delete()
            if antirequisite:
                t = Task.objects.filter(
                    employee=self.employee, type=antirequisite.task_type
                ).first()
                if t:
                    t.delete()
        else:
            due_date = completion_date + self.type.validity_period
            status = TaskStatus.open

            for task in supersedes:
                # If the task due date is greater than the parent due date
                # then we shouldn't update because it will still be valid
                # after the parent task expires.
                if not task.due_date or task.due_date < due_date:
                    task.due_date = due_date
                task.status = status
                task.save()

            self.due_date = due_date
            self.status = status
            self.save()

            if antirequisite:
                t = Task.objects.filter(
                    employee=self.employee, type=antirequisite.task_type
                ).first()
                if t:
                    t.due_date = due_date
                    t.save()

        for task in Task.objects.filter(
            employee=self.employee, type__in=self.type.required_after_self.all()
        ):
            task.recompute_due_date()

        return th

    def incomplete(self, completion_date):
        th = TaskHistory.objects.create(
            employee=self.employee,
            type=self.type,
            status=TaskHistoryStatus.incomplete,
            completion_date=completion_date,
        )

        self.status = TaskStatus.open
        self.save()

        return th

    def recompute_due_date(self):
        if not self.employee.get_required_tasktypes().filter(id=self.type.id).exists():
            self.delete()
            return

        if not self.type.check_capacity(self.employee):
            self.delete()
            return
        else:
            # Migrate task histories in case the rules changed
            TaskHistory.objects.filter(employee=self.employee, type__name=self.type.name).update(
                type=self.type
            )

        type_ids = list(self.type.superseded_by.values_list("id", flat=True))
        type_ids.append(self.type)
        latest_history = (
            TaskHistory.objects.filter(employee=self.employee, type__in=type_ids)
            .order_by("-type__is_one_off", "-expiration_date")
            .first()
        )

        if latest_history and latest_history.type.is_one_off:
            self.delete()
            return

        if latest_history:
            self.due_date = latest_history.completion_date + latest_history.type.validity_period
        else:
            if self.type.required_after_task_type:
                required_after_latest_history = (
                    TaskHistory.objects.filter(
                        employee=self.employee, type=self.type.required_after_task_type
                    )
                    .order_by("-type__is_one_off", "-expiration_date")
                    .first()
                )
                if required_after_latest_history:
                    self.due_date = (
                        required_after_latest_history.completion_date + self.type.required_within
                    )
                else:
                    self.due_date = None
            else:
                self.type.refresh_from_db()
                self.due_date = self.employee.date_of_hire + self.type.required_within

        self.save()


class TrainingEvent(TimeStampedModel):
    training_for = models.ForeignKey(TaskType, on_delete=models.CASCADE)
    attendees = models.ManyToManyField(Employee)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    completed = models.BooleanField(default=False)
    employee_tasks = models.ManyToManyField(Task, blank=True, related_name="training_events")
    location = models.TextField()
    note = models.TextField(blank=True)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)

    def clean(self):
        if not self.training_for.is_training:
            raise ValidationError({"training_for": ["TaskType must be a training."]})

    def __str__(self):
        return "%s :  %s - %s" % (
            self.training_for,
            localtime(self.start_time),
            localtime(self.end_time),
        )

    def finish(self, incomplete_attendee_ids=[], credit_hours=0):
        """Complete the task for the attendees."""
        completion_date = self.end_time

        for task in Task.objects.filter(type=self.training_for, employee__in=self.attendees.all()):
            if task.employee_id in incomplete_attendee_ids:
                task.incomplete(completion_date)
            else:
                if self.training_for.is_continuing_education():
                    if not credit_hours:
                        duration = self.end_time - self.start_time
                        credit_hours = duration.total_seconds() / 60 / 60
                task.complete(completion_date, credit_hours)
        self.completed = True
        self.save()


class PositionGroup(TimeStampedModel):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


def facility_question_slug_populate_from(instance):
    return instance.question


def facility_question_slug_slugify(value):
    return slugify(value)


Languages = Enumeration(
    (1, "english", "English"),
    (2, "spanish", "Spanish"),
)


class Course(TimeStampedModel):
    task_type = models.OneToOneField(TaskType, related_name="course", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(verbose_name="agenda")
    objective = models.TextField()
    duration = models.CharField(max_length=255)
    minimum_score = models.IntegerField(default=0)
    published = models.BooleanField(default=False)
    language = models.SmallIntegerField(choices=Languages, default=Languages.english)
    statement_required = models.BooleanField(default=False)
    trainer = models.ForeignKey("Trainer", blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class CourseItem(TimeStampedModel):
    AVERAGE_WORDS_PER_SECOND = 3
    DEFAULT_DURATION = 10
    course = models.ForeignKey(Course, related_name="items", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    image = models.ImageField(
        blank=True, null=True, upload_to=random_name_in("trainings/course-item-images")
    )
    min_duration = models.SmallIntegerField(
        blank=True,
        null=True,
        help_text="In seconds. Leave blank to populate with the default.",
    )

    def calculate_default_min_duration(self):
        min_duration = 0
        if self.boolean.exists():
            min_duration += self.DEFAULT_DURATION * self.boolean.count()
        if self.choices.exists():
            min_duration += self.DEFAULT_DURATION * self.choices.count()
        if self.texts.exists():

            def reducer(result, text):
                return result + len(text.question.split() + text.answer.split())

            word_count = reduce(reducer, self.texts.all(), 0)
            min_duration += word_count / self.AVERAGE_WORDS_PER_SECOND
        if self.letter_size_image.exists():
            min_duration += self.DEFAULT_DURATION * self.letter_size_image.count()
        if self.image:
            min_duration += self.DEFAULT_DURATION
        if self.videos.exists():
            min_duration += self.DEFAULT_DURATION
        return min_duration or None

    def save(self, *args, **kwargs):
        if not self.min_duration:
            self.min_duration = self.calculate_default_min_duration()
        super(CourseItem, self).save(*args, **kwargs)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class EmployeeCourse(TimeStampedModel):
    STATUSES = Choices((0, "in_progress", "In Progress"), (1, "completed", "Completed"))
    employee = models.ForeignKey(Employee, related_name="courses", on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name="employee_courses", on_delete=models.CASCADE)
    status = models.IntegerField(choices=STATUSES, default=0)
    score = models.IntegerField(default=0)
    start_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    signature = models.ImageField(
        null=True, blank=True, upload_to=random_name_in("trainings/signatures")
    )

    def __str__(self):
        return "{} ({})".format(self.course.name, self.score)


class EmployeeCourseItem(TimeStampedModel):
    employee = models.ForeignKey(Employee, related_name="course_items", on_delete=models.CASCADE)
    course_item = models.ForeignKey(
        CourseItem, related_name="employee_course_items", on_delete=models.CASCADE
    )
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.course_item.title


class CourseItemText(TimeStampedModel):
    item = models.ForeignKey(CourseItem, null=True, related_name="texts", on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.question


class CourseItemVideo(TimeStampedModel):
    item = models.ForeignKey(
        CourseItem, null=True, related_name="videos", on_delete=models.SET_NULL
    )
    link = models.CharField(max_length=255)
    embedded_url = models.TextField()
    order = models.IntegerField(default=0)
    thumbnail = models.ImageField(
        blank=True,
        null=True,
        upload_to=random_name_in("trainings/course-item-video-thumbnail"),
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.link


class CourseItemBoolean(TimeStampedModel):
    item = models.ForeignKey(
        CourseItem, null=True, related_name="boolean", on_delete=models.CASCADE
    )
    question = models.TextField()
    answer = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.question


class MultiChoiceOption(TimeStampedModel):
    label = models.TextField()

    def __str__(self):
        return self.label

    class Meta:
        ordering = ["id"]


class CourseItemMultiChoice(TimeStampedModel):
    item = models.ForeignKey(
        CourseItem, null=True, related_name="choices", on_delete=models.CASCADE
    )
    question = models.TextField()
    options = models.ManyToManyField(MultiChoiceOption, related_name="choice_options")
    answers = models.ManyToManyField(MultiChoiceOption, related_name="choice_answers")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.question


class CourseItemLetterSizeImage(TimeStampedModel):
    item = models.ForeignKey(
        CourseItem,
        null=True,
        related_name="letter_size_image",
        on_delete=models.CASCADE,
    )
    image = models.ImageField(
        blank=True,
        null=True,
        upload_to=random_name_in("trainings/course-letter-size-images"),
    )
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.item.title + " Image {}".format(self.order)


class Trainer(TimeStampedModel):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    signature = models.ImageField(
        null=True, blank=True, upload_to=random_name_in("trainings/trainers/signatures")
    )
    contact_info = models.TextField()
    endorsements = models.TextField()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.full_name


class FacilityQuestion(TimeStampedModel):
    question = models.CharField(max_length=512)
    is_license = models.BooleanField(default=False)
    description = models.TextField()
    slug = AutoSlugField(
        populate_from=facility_question_slug_populate_from,
        slugify=facility_question_slug_slugify,
        editable=True,
        unique=True,
    )

    states_supported = models.ManyToManyField(
        "alfdirectory.State",
        through="FacilityQuestionState",
        blank=True,
        related_name="facility_questions",
    )

    def __str__(self):
        return self.question

    @property
    def abbreviation(self):
        output = self.description.replace("License", "")
        return "".join([e[0].upper() for e in output.split()])


class FacilityQuestionRule(TimeStampedModel):
    facility_question = models.ForeignKey(
        FacilityQuestion, related_name="rules", on_delete=models.CASCADE
    )
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    responsibility = models.ForeignKey(Responsibility, on_delete=models.CASCADE)

    class Meta:
        unique_together = "facility_question", "position", "responsibility"

    def __str__(self):
        return "%s position must have %s responsibility" % (
            self.position,
            self.responsibility,
        )


class Antirequisite(TimeStampedModel):
    """
    Antirequisites can un-require an employee from
    taking a task type.  This effect takes
    place only if the employee was hired after the
    `valid_after_hire_date` of the antirequisite.  If
    the employee has taken `antirequisite_of` before
    their date of hire then they no longer have to take `task_type`.
    If the employee was not hired after the `valid_after_hire_date` or
    they completed the `antirequisite_of` after their date of hire
    then the antirequisite has no effect.
    """

    task_type = models.ForeignKey("TaskType", on_delete=models.CASCADE)
    antirequisite_of = models.ForeignKey(
        "TaskType",
        related_name="antirequisite_of",
        on_delete=models.CASCADE,
    )
    valid_after_hire_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = "task_type", "antirequisite_of"

    def __str__(self):
        return self.task_type.name + " is antirequisite of " + self.antirequisite_of.name


class GlobalRequirement(TimeStampedModel):
    task_type = models.OneToOneField("TaskType", on_delete=models.CASCADE)

    def __str__(self):
        return str(self.task_type)

    def __repr__(self):
        return "<GlobalRequirement: {}>".format(self.pk)


class FacilityDefault(TimeStampedModel):
    facility = models.OneToOneField("Facility", related_name="default", on_delete=models.CASCADE)
    employee_responsibility = models.IntegerField(choices=BOOLEAN_INTS, default=-1)

    def __str__(self):
        return "Default values for " + self.facility.name


class FacilityQuestionState(TimeStampedModel):
    question = models.ForeignKey("FacilityQuestion", on_delete=models.CASCADE)
    state = models.ForeignKey("alfdirectory.State", on_delete=models.CASCADE)


class SponsorState(TimeStampedModel):
    state = models.ForeignKey("alfdirectory.State", on_delete=models.CASCADE)
    sponsor = models.ForeignKey("subscriptions.Sponsor", on_delete=models.CASCADE)
