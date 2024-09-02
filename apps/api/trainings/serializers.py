import logging

from django.db import IntegrityError, transaction
from django.utils import timezone

from dateutil.parser import parse as parse_date
from expander import ExpanderSerializerMixin
from rest_framework import serializers
from rest_framework.serializers import FileField, ModelSerializer

from apps.api.fields import TimedeltaField, USPhoneNumberField, USSocialSecurityNumberField
from apps.api.trainings.course_serializers import CourseSerializer, CourseSimpleSerializer
from apps.api.users.serializers import UserSerializer
from apps.facilities.models import UserInvite
from apps.trainings.models import (
    CustomTaskType,
    CustomTaskTypePrerequisite,
    CustomTaskTypeRequiredFor,
    CustomTaskTypeSupersede,
    Employee,
    Facility,
    FacilityQuestion,
    Position,
    PositionGroup,
    Responsibility,
    ResponsibilityEducationRequirement,
    Task,
    TaskHistory,
    TaskHistoryCertificate,
    TaskHistoryCertificatePage,
    TaskHistoryStatus,
    TaskType,
    TaskTypeEducationCredit,
    TrainingEvent,
)

logger = logging.getLogger(__name__)


class ResponsibilitySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Responsibility
        fields = (
            "id",
            "name",
        )


class ResponsibilityReadWriteSerializer(serializers.ModelSerializer):
    class _PositionSerializer(serializers.ModelSerializer):
        class Meta:
            model = Position
            fields = (
                "id",
                "name",
            )

    positions = _PositionSerializer(source="position_set", many=True, read_only=True)

    class Meta:
        model = Responsibility
        fields = "__all__"
        read_only_fields = ("facility",)

    def create(self, validated_data):
        validated_data["facility"] = self.context["request"].facility
        return super(ResponsibilityReadWriteSerializer, self).create(validated_data)


class PositionSerializer(serializers.ModelSerializer):
    class _ResponsibilitySerializer(serializers.ModelSerializer):
        class Meta:
            model = Responsibility
            fields = "__all__"

    responsibilities = _ResponsibilitySerializer(many=True)

    class Meta:
        model = Position
        fields = "__all__"
        read_only_fields = ("facility",)

    def create(self, validated_data):
        validated_data["facility"] = self.context["request"].facility
        return super().create(PositionSerializer, self).create(validated_data)


class TaskTypeBaseSerializer(serializers.ModelSerializer):
    required_within = TimedeltaField()
    validity_period = TimedeltaField()
    is_continuing_education = serializers.SerializerMethodField()

    def get_is_continuing_education(self, task_type):
        return task_type.is_continuing_education()


class TaskTypeSimpleSerializer(ExpanderSerializerMixin, TaskTypeBaseSerializer):
    course = CourseSimpleSerializer()

    class Meta:
        model = TaskType
        fields = (
            "id",
            "name",
            "required_within",
            "validity_period",
            "course",
            "is_one_off",
            "is_training",
            "hide_in_lms",
            "is_continuing_education",
            "required_for",
            "rule",
            "image",
            "external_training_url",
        )
        expandable_fields = {"course": CourseSerializer}


class TaskTypeWriteSerializer(TaskTypeBaseSerializer):
    def __init__(self, *args, **kwargs):
        super(TaskTypeWriteSerializer, self).__init__(*args, **kwargs)
        if kwargs.get("data"):
            if kwargs["data"].get("is_one_off"):
                self.fields["validity_period"].required = False

    class Meta:
        model = TaskType
        fields = (
            "id",
            "name",
            "is_training",
            "hide_in_lms",
            "is_one_off",
            "required_within",
            "validity_period",
            "required_for",
            "prerequisites",
            "supersedes",
            "rule",
            "is_continuing_education",
            "image",
        )

    def create(self, validated_data):
        validated_data["facility"] = self.context["request"].facility
        return super(TaskTypeWriteSerializer, self).create(validated_data)


class CustomTaskTypeWriteSerializer(serializers.ModelSerializer):
    required_within = TimedeltaField()
    validity_period = TimedeltaField()
    prerequisites = serializers.PrimaryKeyRelatedField(queryset=TaskType.objects.all(), many=True)
    supersedes = serializers.PrimaryKeyRelatedField(queryset=TaskType.objects.all(), many=True)
    required_for = serializers.PrimaryKeyRelatedField(
        queryset=Responsibility.objects.all(), many=True
    )

    class Meta:
        model = CustomTaskType
        fields = (
            "id",
            "name",
            "is_training",
            "is_one_off",
            "required_within",
            "validity_period",
            "required_for",
            "prerequisites",
            "supersedes",
            "rule",
            "description",
        )

    def __init__(self, *args, **kwargs):
        super(CustomTaskTypeWriteSerializer, self).__init__(*args, **kwargs)
        if kwargs.get("data"):
            if kwargs["data"].get("is_one_off"):
                self.fields["validity_period"].required = False

    def create(self, validated_data):
        validated_data["facility"] = self.context["request"].facility

        prerequisites = validated_data.pop("prerequisites")
        supersedes = validated_data.pop("supersedes")
        required_for = validated_data.pop("required_for")

        custom_task_type = super(CustomTaskTypeWriteSerializer, self).create(validated_data)

        CustomTaskTypePrerequisite.objects.bulk_create(
            CustomTaskTypePrerequisite(custom_task_type=custom_task_type, prerequisite=prerequisite)
            for prerequisite in prerequisites
        )
        CustomTaskTypeSupersede.objects.bulk_create(
            CustomTaskTypeSupersede(custom_task_type=custom_task_type, supersede=supersede)
            for supersede in supersedes
        )
        CustomTaskTypeRequiredFor.objects.bulk_create(
            CustomTaskTypeRequiredFor(
                custom_task_type=custom_task_type, required_for=responsibility
            )
            for responsibility in required_for
        )
        return custom_task_type


class CustomTaskTypeReadSerializer(serializers.ModelSerializer):
    required_within = TimedeltaField()
    validity_period = TimedeltaField()
    required_for = serializers.SerializerMethodField()
    prerequisites = serializers.SerializerMethodField()
    supersedes = serializers.SerializerMethodField()

    class Meta:
        model = CustomTaskType
        fields = "__all__"

    def get_prerequisites(self, obj):
        return [
            TaskTypeSimpleSerializer(prerequisite.prerequisite).data
            for prerequisite in obj.prerequisites.all()
        ]

    def get_supersedes(self, obj):
        return [
            TaskTypeSimpleSerializer(supersedes.supersede).data
            for supersedes in obj.supersedes.all()
        ]

    def get_required_for(self, obj):
        return [
            ResponsibilitySimpleSerializer(required_for.required_for).data
            for required_for in obj.required_for.all()
        ]


class EmployeeBaseSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    phone_number = USPhoneNumberField(required=False, allow_blank=True)
    ssn = USSocialSecurityNumberField(required=False, allow_blank=True)

    def get_full_name(self, employee):
        return "{} {}".format(employee.first_name, employee.last_name)


class EmployeeSimpleSerializer(EmployeeBaseSerializer):
    class Meta:
        model = Employee
        fields = (
            "id",
            "first_name",
            "last_name",
            "full_name",
        )


class EmployeeCreateCompletedTaskSerializer(serializers.Serializer):
    type_id = serializers.IntegerField()
    completion_date = serializers.DateField()
    credit_hours = serializers.IntegerField(min_value=0, default=0)


class EmployeeCreateSerializer(EmployeeBaseSerializer):
    completed_tasks = EmployeeCreateCompletedTaskSerializer(
        many=True,
        default=tuple(),
        write_only=True,
    )

    class Meta:
        model = Employee
        fields = "__all__"
        read_only_fields = ("facility",)

    def to_internal_value(self, data):
        if data.get("date_of_hire"):
            data["date_of_hire"] = parse_date(data.get("date_of_hire")).date()
        return super().to_internal_value(data)

    def validate_positions(self, positions):
        if len(positions) < 1:
            raise serializers.ValidationError("The employee must have at least one position")
        return positions

    def create(self, validated_data):
        tasks_data = validated_data.pop("completed_tasks")
        validated_data["facility"] = self.context["request"].facility

        with transaction.atomic():
            employee = super(EmployeeCreateSerializer, self).create(validated_data)
            for task_data in tasks_data:
                completion_date = task_data.pop("completion_date")
                credit_hours = task_data.pop("credit_hours")
                task = Task.objects.create(employee=employee, **task_data)
                task.complete(completion_date, credit_hours)
        return employee


class UserInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInvite
        fields = (
            "id",
            "email",
            "phone_number",
            "role",
            "status",
            "employee",
        )


class EmployeeReadSerializer(EmployeeBaseSerializer):
    positions = PositionSerializer(many=True)
    other_responsibilities = ResponsibilityReadWriteSerializer(many=True)
    facility_name = serializers.CharField(source="facility.name", read_only=True)
    user = serializers.SerializerMethodField()
    invites = UserInviteSerializer(many=True)

    class Meta:
        model = Employee
        fields = "__all__"
        read_only_fields = ("facility",)

    def get_user(self, obj):
        try:
            if obj.user:
                return UserSerializer(obj.user).data
        except Exception:
            pass
        return None


class EmployeeEditSerializer(EmployeeBaseSerializer):
    class Meta:
        model = Employee
        fields = (
            "first_name",
            "last_name",
            "email",
            "picture",
            "address",
            "address2",
            "city",
            "state",
            "zip_field",
            "invite_code",
            "facility",
            "user",
            "date_of_hire",
            "positions",
            "other_responsibilities",
            "ssn",
            "phone_number",
            "job_description",
            "application_references",
            "date_of_birth",
            "is_reactivated",
            "is_active",
            "code_verified",
            "receives_emails",
            "deactivation_reason",
            "deactivation_date",
            "deactivation_note",
        )
        read_only_fields = (
            "facility",
            "user",
        )

    def validate_positions(self, positions):
        if len(positions) < 1:
            raise serializers.ValidationError("The employee must have at least one position")
        return positions

    def update(self, instance, validated_data):
        employee = super(EmployeeEditSerializer, self).update(instance, validated_data)
        if "email" in validated_data:
            email = validated_data["email"]
            user = employee.user
            if user:
                user.email = email
                user.save()
        return employee


class FacilityQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilityQuestion
        fields = ("id", "question", "is_license", "description", "slug")


class FacilitySerializer(ExpanderSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = (
            "id",
            "name",
            "contact_phone",
            "contact_email",
            "directory_facility",
            "capacity",
            "questions",
            "address_line1",
            "address_line2",
            "address_city",
            "state",
            "address_zipcode",
            "primary_administrator_name",
            "contact_phone",
            "contact_email",
            "is_resident_module_enabled",
            "is_lms_module_enabled",
            "is_staff_module_enabled",
        )
        expandable_fields = {
            "questions": (FacilityQuestionSerializer, (), {"many": True}),
        }


class EmployeeReadExpandableSerializer(ExpanderSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = (
            "id",
            "facility",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "ssn",
            "picture",
            "date_of_birth",
            "positions",
            "date_of_hire",
            "address",
            "address2",
            "city",
            "state",
            "zip_field",
            "invite_code",
            "receives_emails",
            "user",
        )
        expandable_fields = {
            "facility": FacilitySerializer,
            "user": UserSerializer,
            "positions": (PositionSerializer, (), {"many": True}),
        }


class TaskHistoryCertificateSerializer(serializers.ModelSerializer):
    certificate1 = FileField(write_only=True)
    certificate2 = FileField(required=False, write_only=True)
    certificate3 = FileField(required=False, write_only=True)
    num_pages = serializers.SerializerMethodField()
    uploaded_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = TaskHistoryCertificate
        fields = (
            "certificate1",
            "certificate2",
            "certificate3",
            "uploaded_at",
            "num_pages",
        )

    def get_num_pages(self, obj):
        return obj.pages.count()

    def create(self, validated_data):
        validated_data["task_history"] = self.context["task_history"]
        certificate_pages = []
        for i in range(1, 4):
            if "certificate{}".format(i) in validated_data:
                certificate_pages.append(validated_data.pop("certificate{}".format(i)))
        certificate = super(TaskHistoryCertificateSerializer, self).create(validated_data)
        TaskHistoryCertificatePage.objects.bulk_create(
            [
                TaskHistoryCertificatePage(certificate=certificate, page=page)
                for page in certificate_pages
            ]
        )
        return certificate


class TrainingEventReadSerializer(serializers.ModelSerializer):
    attendees = EmployeeSimpleSerializer(many=True)
    training_for = TaskTypeSimpleSerializer()
    training_for_name = serializers.CharField(source="training_for.name")
    flyer_url = serializers.HyperlinkedIdentityField(view_name="trainingevent-flyer")

    class Meta:
        model = TrainingEvent
        fields = (
            "id",
            "training_for",
            "start_time",
            "end_time",
            "location",
            "completed",
            "attendees",
            "training_for_name",
            "flyer_url",
            "note",
        )


class TrainingEventWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingEvent
        fields = (
            "id",
            "facility",
            "training_for",
            "start_time",
            "end_time",
            "location",
            "completed",
            "attendees",
            "note",
        )
        read_only_fields = (
            "completed",
            "facility",
        )
        extra_kwargs = {"attendees": {"required": False, "allow_empty": True}}

    def create(self, validated_data):
        validated_data["facility"] = self.context["request"].facility
        return super(TrainingEventWriteSerializer, self).create(validated_data)


class DefaultPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = "__all__"
        read_only_fields = ("facility",)


class DefaultTaskTypeEducationCreditSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskTypeEducationCredit
        fields = "__all__"

    def create(self, validated_data):
        validated_data["facility"] = self.context["request"].facility
        return super(DefaultTaskTypeEducationCreditSerializer, self).create(validated_data)


class ResponsibilityEducationRequirementWriteSerializer(ModelSerializer):
    timeperiod = TimedeltaField()

    class Meta:
        model = ResponsibilityEducationRequirement
        fields = "__all__"

    def validate(self, data):
        """
            Removes the "start_over" field from the dictionary of submitted
        values if the user is not admin, because only an admin can edit
        that value.
        """
        request = self.context.get("request")

        if request:
            if not request.user.is_superuser:
                data.pop("start_over", None)

        return data


class ResponsibilityEducationRequirementReadSerializer(ModelSerializer):
    responsibility = ResponsibilitySimpleSerializer()
    interval_base = TaskTypeSimpleSerializer()
    type_name = serializers.CharField(source="get_type_display", read_only=True)
    timeperiod = TimedeltaField()

    class Meta:
        model = ResponsibilityEducationRequirement
        fields = "__all__"


class TaskWriteSerializer(serializers.ModelSerializer):
    type_name = serializers.CharField(source="type.name", read_only=True)

    class Meta:
        model = Task
        fields = "__all__"


class ScheduledEventSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()

    class Meta:
        model = TrainingEvent
        fields = (
            "id",
            "date",
            "start_time",
            "end_time",
            "location",
            "note",
            "completed",
            "facility",
        )

    def get_date(self, obj):
        return obj.start_time


class TaskReadSerializer(serializers.ModelSerializer):
    employee = EmployeeSimpleSerializer()
    type = TaskTypeSimpleSerializer()
    status_name = serializers.CharField(source="get_status_display", read_only=True)
    scheduled_event = serializers.SerializerMethodField()
    online_course = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = "__all__"

    def get_scheduled_event(self, obj):
        scheduled_event = obj.scheduled_event
        if scheduled_event:
            return ScheduledEventSerializer(scheduled_event).data
        return None

    def get_online_course(self, obj):
        request = self.context.get("request", None)
        employee = getattr(obj, "employee", None)
        task_type = getattr(obj, "type", None)
        if request and employee:
            if request.user and request.user == getattr(employee, "user", None):
                course = getattr(task_type, "course", None)
                if course and course.published:
                    return True
        return False


class TaskHistoryReadSerializer(serializers.ModelSerializer):
    employee = EmployeeSimpleSerializer()
    type = TaskTypeSimpleSerializer()
    status_name = serializers.CharField(source="get_status_display", read_only=True)
    certificate = TaskHistoryCertificateSerializer()
    completion_date = serializers.DateField(read_only=True)
    expiration_date = serializers.DateField(read_only=True)

    class Meta:
        model = TaskHistory
        fields = "__all__"


class PositionGroupReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PositionGroup
        read_only_fields = "id", "name"
        fields = "__all__"


class TaskHistoryCreateSerializer(serializers.ModelSerializer):
    type_name = serializers.CharField(source="type.name", read_only=True)
    is_training = serializers.CharField(source="type.is_training", read_only=True)
    is_one_off = serializers.CharField(source="type.is_one_off", read_only=True)
    certificate1 = FileField(required=False)
    certificate2 = FileField(required=False)
    certificate3 = FileField(required=False)

    class Meta:
        model = TaskHistory
        fields = (
            "id",
            "employee",
            "type",
            "completion_date",
            "expiration_date",
            "status",
            "credit_hours",
            "type_name",
            "is_training",
            "is_one_off",
            "certificate1",
            "certificate2",
            "certificate3",
        )
        read_only_fields = (
            "id",
            "expiration_date",
        )

    def validate(self, data):
        credit_hours = data.get("credit_hours", 0)
        if not credit_hours:
            if TaskTypeEducationCredit.objects.filter(tasktype=data["type"]).exists():
                raise serializers.ValidationError(
                    "This task is worth continuing education credits.  You "
                    "must enter the number of credit hours."
                )
        return data

    def create(self, validated_data):
        certificate_pages = []
        for i in range(1, 4):
            if "certificate{}".format(i) in validated_data:
                certificate_pages.append(validated_data.pop("certificate{}".format(i)))

        task = Task.objects.create(type=validated_data["type"], employee=validated_data["employee"])
        if validated_data["status"] == TaskHistoryStatus.completed:
            th = task.complete(
                validated_data["completion_date"], validated_data.get("credit_hours", 0)
            )
        else:
            th = task.incomplete(validated_data["completion_date"])

        if certificate_pages:
            certificate = TaskHistoryCertificate.objects.create(task_history=th)
            TaskHistoryCertificatePage.objects.bulk_create(
                [
                    TaskHistoryCertificatePage(certificate=certificate, page=page)
                    for page in certificate_pages
                ]
            )
        return th

    def to_representation(self, obj):
        return TaskHistoryReadSerializer().to_representation(obj)


class TaskReadExpandSerializer(ExpanderSerializerMixin, TaskReadSerializer):
    class Meta:
        model = Task
        fields = (
            "id",
            "due_date",
            "status",
            "employee",
            "type",
            "antirequisite",
            "scheduled_event",
            "status_name",
            "online_course",
        )
        expandable_fields = {
            "employee": EmployeeReadSerializer,
            "type": TaskTypeSimpleSerializer,
        }


class TaskHistoryExpandedSerializer(ExpanderSerializerMixin, TaskHistoryReadSerializer):
    class Meta:
        model = Task
        fields = "__all__"
        expandable_fields = {"type": TaskTypeSimpleSerializer}


class TaskTypeReadSerializer(TaskTypeBaseSerializer):
    class _TaskTypeEducationCreditSerializer(serializers.ModelSerializer):
        class Meta:
            model = TaskTypeEducationCredit
            fields = "__all__"

    class _EducationRequirementSerializer(ModelSerializer):
        class Meta:
            model = ResponsibilityEducationRequirement
            fields = "__all__"

        timeperiod = TimedeltaField()
        responsibility = ResponsibilitySimpleSerializer()

    # TODO change this to a serializer that doesnt include positions after
    # ALF-117 is fixed.
    required_for = ResponsibilitySimpleSerializer(many=True)
    prerequisites = TaskTypeSimpleSerializer(many=True)
    education_credits = _TaskTypeEducationCreditSerializer(read_only=True, many=True)
    course = CourseSerializer(read_only=True)
    education_requirements = _EducationRequirementSerializer(
        source="responsibilityeducationrequirement_set", read_only=True, many=True
    )

    class Meta:
        model = TaskType
        fields = "__all__"


class VerifyInviteSerializer(serializers.Serializer):
    code = serializers.CharField()

    def create(self, validated_data):
        employee = Employee.objects.filter(invite_code=validated_data.get("code")).first()
        if not employee:
            raise serializers.ValidationError({"code": "Invalid invitation code"})
        employee.code_verified = True
        employee.save()
        return employee


class PositionCloudCareSerializer(ModelSerializer):
    class Meta:
        model = Position
        fields = ("id", "name")


class EmployeeCloudCareSerializer(ModelSerializer):
    positions_detail = PositionCloudCareSerializer(source="positions", many=True, read_only=True)
    positions = serializers.PrimaryKeyRelatedField(
        queryset=Position.objects.all(), many=True, write_only=True
    )
    date_of_hire = serializers.DateField(read_only=True)

    class Meta:
        model = Employee
        fields = (
            "id",
            "first_name",
            "last_name",
            "positions",
            "positions_detail",
            "facility",
            "date_of_hire",
        )

    def create(self, validated_data):
        validated_data["date_of_hire"] = timezone.now().date()
        return super(EmployeeCloudCareSerializer, self).create(validated_data)


class EmployeeInviteSerializer(serializers.Serializer):
    employees = serializers.ListField(child=serializers.IntegerField())

    def create(self, validated_data):
        invited = []
        not_invited = []
        employees = Employee.objects.filter(id__in=validated_data.get("employees"))
        for employee in employees:
            try:
                invite = UserInvite.objects.create(
                    role="trainings_user",
                    email=employee.email,
                    facility=employee.facility,
                    employee=employee,
                    can_see_residents=False,
                    can_see_staff=False,
                    invited_by=self.context["request"].user,
                )
            except IntegrityError:
                not_invited.append(EmployeeSimpleSerializer(employee).data)
                continue
            except AttributeError:
                not_invited.append(EmployeeSimpleSerializer(employee).data)
                continue
            except Exception as e:
                not_invited.append(EmployeeSimpleSerializer(employee).data)
                logger.error(e.message)
                continue
            invited.append(UserInviteSerializer(invite).data)

        return {"invited": invited, "not_invited": not_invited}
