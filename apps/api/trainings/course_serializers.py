import datetime

from django.db.models import Q
from django.utils import timezone

from expander import ExpanderSerializerMixin
from rest_framework import serializers

from apps.api.fields import ThumbnailImageField
from apps.trainings.models import (
    Course,
    CourseItem,
    CourseItemBoolean,
    CourseItemLetterSizeImage,
    CourseItemMultiChoice,
    CourseItemText,
    CourseItemVideo,
    EmployeeCourse,
    EmployeeCourseItem,
    MultiChoiceOption,
    Task,
    TaskType,
)


class CourseItemTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseItemText
        fields = (
            "id",
            "item",
            "question",
            "answer",
            "order",
        )
        read_only_fields = ("course",)


class CourseItemVideoSerializer(serializers.ModelSerializer):
    video_id = serializers.SerializerMethodField()

    class Meta:
        model = CourseItemVideo
        fields = (
            "id",
            "item",
            "link",
            "video_id",
            "embedded_url",
            "thumbnail",
            "order",
        )
        read_only_fields = ("course",)

    def get_video_id(self, video):
        return video.link.split("/")[-1]


class CourseItemBooleanSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseItemBoolean
        fields = (
            "id",
            "item",
            "question",
            "answer",
            "order",
        )
        read_only_fields = ("course",)


class MultiChoiceOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultiChoiceOption
        fields = ("id", "label")


class CourseItemMultiChoiceSerializer(ExpanderSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = CourseItemMultiChoice
        fields = (
            "id",
            "item",
            "question",
            "options",
            "answers",
            "order",
        )
        read_only_fields = ("course",)
        expandable_fields = {
            "options": (MultiChoiceOptionSerializer, (), {"many": True}),
            "answers": (MultiChoiceOptionSerializer, (), {"many": True}),
        }


class CourseItemLetterSizeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseItemLetterSizeImage
        fields = (
            "id",
            "item",
            "image",
            "order",
        )
        read_only_fields = ("course",)


class CourseItemMultiChoiceCreateSerializer(ExpanderSerializerMixin, serializers.ModelSerializer):
    options = serializers.ListField(child=MultiChoiceOptionSerializer())
    answers = serializers.ListField(child=MultiChoiceOptionSerializer())

    class Meta:
        model = CourseItemMultiChoice
        fields = (
            "id",
            "item",
            "question",
            "options",
            "answers",
            "order",
        )
        read_only_fields = ("course",)

    def create(self, validated_data):
        options = validated_data.pop("options", [])
        answers = validated_data.pop("answers", [])
        multi_choice = CourseItemMultiChoice.objects.create(**validated_data)

        if options:
            for item in options:
                option = MultiChoiceOption.objects.create(**item)
                multi_choice.options.add(option)

        if answers:
            for item in answers:
                option = multi_choice.options.filter(label=item["label"]).first()
                if option:
                    multi_choice.answers.add(option)

        return multi_choice


class CourseItemSerializer(ExpanderSerializerMixin, serializers.ModelSerializer):
    texts = CourseItemTextSerializer(many=True, read_only=True)
    videos = CourseItemVideoSerializer(many=True, read_only=True)
    letter_size_image = CourseItemLetterSizeImageSerializer(many=True, read_only=True)
    boolean = CourseItemBooleanSerializer(many=True, read_only=True)
    choices = CourseItemMultiChoiceSerializer(many=True, read_only=True)
    started_at = serializers.SerializerMethodField()

    class Meta:
        model = CourseItem
        fields = (
            "id",
            "course",
            "title",
            "order",
            "image",
            "texts",
            "videos",
            "letter_size_image",
            "boolean",
            "choices",
            "started_at",
            "min_duration",
        )
        read_only_fields = (
            "texts",
            "videos",
            "letter_size_image",
            "boolean",
            "choices",
            "started_at",
        )
        expandable_fields = {
            "videos": (CourseItemVideoSerializer, (), {"many": True}),
            "letter_size_image": (
                CourseItemLetterSizeImageSerializer,
                (),
                {"many": True},
            ),
            "boolean": (CourseItemBooleanSerializer, (), {"many": True}),
            "choices": (CourseItemMultiChoiceSerializer, (), {"many": True}),
        }

    def get_started_at(self, course_item):
        try:
            employee = self.context["request"].user.employee
            employee_course_item = EmployeeCourseItem.objects.filter(
                course_item=course_item, employee=employee
            ).first()
            if employee_course_item:
                return employee_course_item.started_at
            else:
                return None
        except Exception:
            return None


class CourseTakenSerializer(serializers.ModelSerializer):
    status_name = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeCourse
        fields = (
            "id",
            "employee",
            "course",
            "status",
            "status_name",
            "score",
            "start_date",
            "completed_date",
        )

    def get_status_name(self, employee_course):
        return EmployeeCourse.STATUSES[employee_course.status][1]


class CourseSerializer(ExpanderSerializerMixin, serializers.ModelSerializer):
    course_taken = serializers.SerializerMethodField()
    max_points = serializers.SerializerMethodField()
    last_started_course_item = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            "id",
            "task_type",
            "name",
            "description",
            "objective",
            "duration",
            "published",
            "items",
            "course_taken",
            "minimum_score",
            "max_points",
            "last_started_course_item",
            "language",
            "statement_required",
        )
        read_only_fields = ("items",)
        expandable_fields = {
            "items": (CourseItemSerializer, (), {"many": True}),
        }

    def get_course_taken(self, course):
        try:
            employee = self.context["request"].user.employee
            return CourseTakenSerializer(
                instance=course.employee_courses.filter(employee=employee), many=True
            ).data
        except Exception:
            return []

    def get_max_points(self, course):
        return (
            course.items.filter(boolean__isnull=False).count()
            + course.items.filter(choices__isnull=False).count()
        )

    def get_last_started_course_item(self, course):
        try:
            employee = self.context["request"].user.employee
            employee_course_item = (
                EmployeeCourseItem.objects.filter(course_item__course=course, employee=employee)
                .order_by("-started_at")
                .first()
            )
            if employee_course_item:
                return employee_course_item.course_item.id
            else:
                return None
        except Exception:
            return None


class TaskTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskType
        fields = (
            "id",
            "image",
        )


class TaskSerializer(serializers.ModelSerializer):
    type = TaskTypeSerializer()

    class Meta:
        model = Task
        fields = ("id", "type")


class CourseOpenSerializer(ExpanderSerializerMixin, serializers.ModelSerializer):

    last_started_course_item = serializers.SerializerMethodField()
    last_completed_course_item = serializers.SerializerMethodField()
    task = serializers.SerializerMethodField()
    current_score = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            "id",
            "duration",
            "description",
            "objective",
            "name",
            "items",
            "minimum_score",
            "last_started_course_item",
            "last_completed_course_item",
            "task",
            "published",
            "language",
            "statement_required",
            "current_score",
        )

        expandable_fields = {
            "items": (CourseItemSerializer, (), {"many": True}),
        }

    def get_task(self, course):
        user = self.context["request"].user
        if not hasattr(user, "employee"):
            raise serializers.ValidationError(
                {
                    "User": "Your user doesn't appear to be linked with an Employee. Please reach out to an administrator"
                }
            )
        employee = user.employee

        try:
            task = Task.objects.get(employee=employee, type=course.task_type)
            return TaskSerializer(task).data
        except Task.DoesNotExist:
            task = Task.objects.create(
                employee=employee,
                type=course.task_type,
                due_date=datetime.date.today(),  # today
                is_optional=True,  # because if the task was not created via signals, it has to be from course dropdown
            )
            return TaskSerializer(task).data

    def get_last_started_course_item(self, course):
        try:
            employee = self.context["request"].user.employee
            employee_course_item = (
                EmployeeCourseItem.objects.filter(course_item__course=course, employee=employee)
                .order_by("-started_at")
                .first()
            )
            return employee_course_item.course_item.id
        except AttributeError:
            return None

    def get_last_completed_course_item(self, course):
        try:
            employee = self.context["request"].user.employee
            employee_course_item = (
                EmployeeCourseItem.objects.filter(
                    course_item__course=course,
                    employee=employee,
                    completed_at__isnull=False,
                )
                .order_by("-completed_at")
                .first()
            )
            return employee_course_item.course_item.id
        except AttributeError:
            return None

    def get_current_score(self, course):
        return EmployeeCourseItem.objects.filter(
            course_item__course=course,
            employee=self.context["request"].user.employee,
            is_correct=True,
        ).count()


class CourseSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = (
            "id",
            "duration",
        )


class CourseItemCreateSerializer(serializers.ModelSerializer):
    texts = serializers.ListField(child=CourseItemTextSerializer(), required=False)
    videos = serializers.ListField(child=CourseItemVideoSerializer(), required=False)
    letter_size_image = serializers.ListField(
        child=CourseItemLetterSizeImageSerializer(), required=False
    )
    boolean = serializers.ListField(child=CourseItemBooleanSerializer(), required=False)
    choices = serializers.ListField(child=CourseItemMultiChoiceCreateSerializer(), required=False)
    course = None

    class Meta:
        model = CourseItem
        fields = (
            "id",
            "course",
            "title",
            "order",
            "texts",
            "videos",
            "letter_size_image",
            "boolean",
            "choices",
        )
        read_only_fields = ("course",)

    def create(self, validated_data):
        texts = validated_data.pop("texts", [])
        videos = validated_data.pop("videos", [])
        letter_size_image = validated_data.pop("letter_size_image", [])
        boolean = validated_data.pop("boolean", [])
        choices = validated_data.pop("choices", [])
        validated_data["course"] = self.course
        course_item = CourseItem.objects.create(**validated_data)
        if texts:
            for item in texts:
                item["item"] = course_item
                CourseItemText.objects.create(**item)

        if videos:
            for item in videos:
                item["item"] = course_item
                CourseItemVideo.objects.create(**item)

        if letter_size_image:
            for item in letter_size_image:
                item["item"] = course_item
                CourseItemLetterSizeImage.objects.create(**item)

        if boolean:
            for item in boolean:
                item["item"] = course_item
                CourseItemBoolean.objects.create(**item)

        if choices:
            for item in choices:
                item["item"] = course_item
                options = item.pop("options")
                answers = item.pop("answers")
                choice = CourseItemMultiChoice.objects.create(**item)
                if options:
                    for opt in options:
                        option = MultiChoiceOption.objects.create(**opt)
                        choice.options.add(option)

                if answers:
                    for ans in answers:
                        option = MultiChoiceOption.objects.create(**ans)
                        choice.answers.add(option)

        return course_item


class EmployeeCourseSerializer(ExpanderSerializerMixin, serializers.ModelSerializer):
    signature = ThumbnailImageField(write_only=True, required=False)
    is_approved = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeCourse
        fields = (
            "id",
            "employee",
            "course",
            "status",
            "score",
            "start_date",
            "completed_date",
            "signature",
            "is_approved",
            "total",
        )
        read_only_fields = ("employee", "course", "status", "is_approved")
        expandable_fields = {
            "course": CourseSerializer,
        }

    def get_total(self, obj):
        return obj.course.items.filter(Q(boolean__isnull=False) | Q(choices__isnull=False)).count()

    def get_is_approved(self, obj):

        if hasattr(obj, "course"):
            return self.context.get("score", 0) >= obj.course.minimum_score
        return False

    def validate(self, validated_data):
        course = self.context["course"]
        employee = self.context["request"].user.employee
        employee_course = EmployeeCourse.objects.filter(course=course, employee=employee).first()

        if self.get_is_approved(employee_course):
            if course and course.statement_required and "signature" not in validated_data:
                raise serializers.ValidationError("Signature required for this course")
        return validated_data

    def create(self, validated_data):
        course = self.context["course"]
        employee = self.context["request"].user.employee
        status = self.context["status"]
        validated_data["course"] = course
        validated_data["employee"] = employee
        validated_data["status"] = status
        validated_data["score"] = self.context.get("score", 0)

        if status == EmployeeCourse.STATUSES.in_progress:
            validated_data["start_date"] = validated_data.pop("start_date", timezone.now().date())
        elif status == EmployeeCourse.STATUSES.completed:
            validated_data["completed_date"] = validated_data.pop(
                "completed_date", timezone.now().date()
            )

        employee_course = EmployeeCourse.objects.filter(course=course, employee=employee).first()
        if employee_course:
            employee_course.status = validated_data.pop("status", 0)
            employee_course.score = validated_data.pop("score", 0)
            employee_course.completed_date = validated_data.pop("completed_date", None)
            employee_course.signature = validated_data.pop("signature", None)
            employee_course.save()
        else:
            employee_course = EmployeeCourse.objects.create(**validated_data)
        return employee_course

    def update(self, instance, validated_data):
        validated_data["score"] = self.context.get("score", 0)
        super().update(instance, validated_data)


class EmployeeCourseItemSerializer(ExpanderSerializerMixin, serializers.ModelSerializer):
    started_at = serializers.DateTimeField(required=False, default=timezone.now)

    class Meta:
        model = EmployeeCourseItem
        fields = ("id", "employee", "course_item", "started_at", "is_correct")
        read_only_fields = ("employee", "course_item")
        expandable_fields = {
            "course_item": CourseItemSerializer,
        }

    def create(self, validated_data):
        course_item = self.context["course_item"]
        employee = self.context["request"].user.employee
        validated_data["course_item"] = course_item
        validated_data["employee"] = employee
        employee_course_item = EmployeeCourseItem.objects.filter(
            course_item=course_item, employee=employee
        ).first()
        if not employee_course_item:
            employee_course_item = EmployeeCourseItem.objects.create(**validated_data)

        employee_course_items_query = EmployeeCourse.objects.filter(
            course=course_item.course, employee=employee
        )
        if not employee_course_items_query:
            started_at = validated_data.get("started_at", timezone.now())
            EmployeeCourse.objects.create(
                course=course_item.course,
                employee=employee,
                start_date=started_at.date(),
            )

        return employee_course_item

    def update(self, instance, validated_data):
        course_item = self.context["course_item"]
        is_correct = self.check_answer_correct(
            self.context["request"].data.get("answer", None), course_item
        )
        validated_data["is_correct"] = is_correct
        validated_data["completed_at"] = timezone.now()
        return super().update(instance, validated_data)

    def check_answer_correct(self, answer, course_item):
        if course_item.boolean.exists():
            return course_item.boolean.first().answer is answer
        elif course_item.choices.exists():
            return course_item.choices.first().answers.first().id == answer
        return False  # Return False for other kinds of answers such as Text or Video
