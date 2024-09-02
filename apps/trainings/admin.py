import csv
import datetime

from django import forms
from django.contrib import admin, messages
from django.db.models import Prefetch
from django.http import HttpResponse, HttpResponseRedirect
from django.templatetags.static import static
from django.urls import re_path, reverse
from django.utils import formats
from django.utils.html import format_html

from apps.trainings.forms import TrainerForm

from ..alfdirectory.models import State
from ..subscriptions.models import FacilityPaymentMethod, Plan, Subscription
from .admin_filters import (
    CapacityFacilityListFilter,
    EmployeeFacilityListFilter,
    EmployeeListFilter,
)
from .continuing_education import compute_compliance_for_employee
from .models import (
    Antirequisite,
    Course,
    CourseItem,
    CourseItemBoolean,
    CourseItemLetterSizeImage,
    CourseItemMultiChoice,
    CourseItemText,
    CourseItemVideo,
    CustomTaskType,
    CustomTaskTypePrerequisite,
    CustomTaskTypeRequiredFor,
    CustomTaskTypeSupersede,
    Employee,
    EmployeeCourse,
    Facility,
    FacilityDefault,
    FacilityQuestion,
    FacilityQuestionRule,
    FacilityQuestionState,
    GlobalRequirement,
    MultiChoiceOption,
    Position,
    PositionGroup,
    Responsibility,
    ResponsibilityEducationRequirement,
    SponsorState,
    Task,
    TaskHistory,
    TaskHistoryCertificate,
    TaskHistoryCertificatePage,
    TaskHistoryStatus,
    TaskType,
    TaskTypeEducationCredit,
    Trainer,
    TrainingEvent,
)
from .tasks import (
    apply_global_requirement,
    reapply_employee_positions,
    reapply_employee_responsibilities,
    regenerate_task_certificates,
)


class FacilityQuestionRuleInline(admin.TabularInline):
    model = FacilityQuestionRule


class CourseItemTextInline(admin.TabularInline):
    model = CourseItemText


class CourseItemVideoInline(admin.TabularInline):
    model = CourseItemVideo


class CourseItemBooleanInline(admin.TabularInline):
    model = CourseItemBoolean


class CourseItemMultiChoiceInline(admin.TabularInline):
    model = CourseItemMultiChoice


class CourseItemLetterSizeImageInline(admin.TabularInline):
    model = CourseItemLetterSizeImage


class CourseItemInline(admin.TabularInline):
    model = CourseItem


class FacilityQuestionRuleAdmin(admin.ModelAdmin):
    model = FacilityQuestionRule
    list_filter = ("facility_question__states_supported",)


class FacilityQuestionAdmin(admin.ModelAdmin):
    model = FacilityQuestion
    inlines = [FacilityQuestionRuleInline]
    exclude = ("slug",)
    list_filter = ("is_license", "states_supported")


class CourseItemAdmin(admin.ModelAdmin):
    model = CourseItem
    list_display = ("id", "title", "course", "order")
    inlines = [
        CourseItemTextInline,
        CourseItemVideoInline,
        CourseItemBooleanInline,
        CourseItemMultiChoiceInline,
        CourseItemLetterSizeImageInline,
    ]
    list_filter = ("course__task_type__facility__state_facility",)


class CourseItemOptionsAdmin(admin.ModelAdmin):
    model = CourseItemMultiChoice
    list_display = ("id", "item", "question", "order")


class TrainerAdmin(admin.ModelAdmin):
    model = Trainer
    form = TrainerForm


class CourseAdmin(admin.ModelAdmin):
    model = Course
    list_display = (
        "id",
        "task_type",
        "name",
        "duration",
        "minimum_score",
        "published",
        "statement_required",
        "language",
    )
    inlines = [
        CourseItemInline,
    ]
    list_filter = ("task_type__facility__state_facility", "statement_required")


class EmployeeCourseAdmin(admin.ModelAdmin):
    model = EmployeeCourse
    list_display = (
        "id",
        "employee",
        "course",
        "status",
        "score",
        "start_date",
        "completed_date",
    )


class MultiChoiceOptionAdmin(admin.ModelAdmin):
    model = MultiChoiceOption


class FacilityDefaultAdmin(admin.StackedInline):
    model = FacilityDefault
    can_delete = False


class FacilityPaymentMethodInline(admin.TabularInline):
    model = FacilityPaymentMethod


def export_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="facilities.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "Facility name",
            "AHCA license #",
            "Capacity",
            "Address",
            "Zip",
            "Staff subscription?",
            "Resident Subscription?",
        ]
    )
    for facility in queryset:
        has_resident_subscription = (
            Subscription.objects.filter(
                facility_id=facility,
                billing_interval__plan__module=Plan.Module.resident,
            )
            .is_active()
            .exists()
        )
        has_staff_subscription = (
            Subscription.objects.filter(
                facility_id=facility, billing_interval__plan__module=Plan.Module.staff
            )
            .is_active()
            .exists()
        )
        writer.writerow(
            [
                facility.name.encode("unicode-escape"),
                facility.directory_facility.license_number.encode("unicode-escape")
                if facility.directory_facility
                else "",
                facility.capacity,
                facility.address.encode("unicode-escape"),
                facility.address_zipcode.encode("unicode-escape"),
                has_staff_subscription,
                has_resident_subscription,
            ]
        )

    return response


class FacilityAdmin(admin.ModelAdmin):
    change_form_template = "trainings/admin/trainings/facilities/change_form.html"
    list_display = (
        "id",
        "name",
        "contact_phone",
        "contact_email",
        "fcc_signup",
        "state_facility",
    )
    search_fields = ("name",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "directory_facility",
                    "capacity",
                    "questions",
                    "npi",
                    "tax_id",
                    "bought_ebook",
                    "created",
                    "admin_signature",
                )
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "address_line1",
                    "address_line2",
                    "address_county",
                    "address_city",
                    "state_facility",
                    "address_zipcode",
                    "point",
                )
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "primary_administrator_name",
                    "contact_phone",
                    "contact_email",
                )
            },
        ),
        (
            "Modules",
            {
                "fields": (
                    "is_resident_module_enabled",
                    "is_lms_module_enabled",
                    "fcc_signup",
                    "is_staff_module_enabled",
                )
            },
        ),
        (
            "Sponsored Status",
            {"fields": ("sponsored_access", "opted_in_sponsorship_date")},
        ),
    )
    readonly_fields = ("created",)
    inlines = [FacilityDefaultAdmin, FacilityPaymentMethodInline]
    list_filter = (
        CapacityFacilityListFilter,
        "bought_ebook",
        "fcc_signup",
        "state_facility",
    )
    actions = [export_csv]

    def response_change(self, request, obj):
        if "_regen-certs" in request.POST and obj:
            regenerate_task_certificates.delay(obj.pk)
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)


class TaskTypeAdminForm(forms.ModelForm):
    class Meta:
        model = TaskType
        fields = (
            "name",
            "is_training",
            "hide_in_lms",
            "is_one_off",
            "required_within",
            "required_after_task_type",
            "validity_period",
            "required_for",
            "facility",
            "prerequisites",
            "supersedes",
            "rule",
            "image",
            "min_capacity",
            "max_capacity",
            "external_training_required",
            "external_training_url",
        )

    def __init__(self, *args, **kwargs):
        super(TaskTypeAdminForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields["supersedes"].queryset = TaskType.objects.exclude(pk=self.instance.pk)
            self.fields["prerequisites"].queryset = TaskType.objects.exclude(pk=self.instance.pk)
            if "external_training_required" in self.data:
                self.fields["external_training_url"].required = True


class CustomTaskTypeAdminForm(forms.ModelForm):
    class Meta:
        model = CustomTaskType
        fields = (
            "is_request",
            "description",
            "name",
            "is_training",
            "is_one_off",
            "required_within",
            "validity_period",
            "facility",
            "rule",
        )


class TaskTypeAdmin(admin.ModelAdmin):
    form = TaskTypeAdminForm
    list_display = (
        "name",
        "required_within",
        "validity_period",
        "facility",
        "is_global_requirement",
    )
    list_filter = (
        "required_within",
        "validity_period",
        "facility",
        "facility__state_facility",
    )

    def is_global_requirement(self, task_type):
        icon = "icon-yes.svg" if task_type.is_global_requirement() else "icon-no.svg"
        img_src = static(f"admin/img/{icon}")
        html_content = f"<img src='{img_src}' />"
        return format_html(html_content)


class CustomTaskTypeSupersedeAdmin(admin.StackedInline):
    model = CustomTaskTypeSupersede
    extra = 0


class CustomTaskTypePrerequisitesAdmin(admin.StackedInline):
    model = CustomTaskTypePrerequisite
    extra = 0


class CustomTaskTypeRequiredForAdmin(admin.StackedInline):
    model = CustomTaskTypeRequiredFor
    extra = 0


class CustomTaskTypeAdmin(admin.ModelAdmin):
    form = CustomTaskTypeAdminForm
    list_display = (
        "name",
        "required_within",
        "validity_period",
        "facility",
        "is_request",
    )
    list_filter = "required_within", "validity_period", "facility", "is_request"
    inlines = [
        CustomTaskTypeSupersedeAdmin,
        CustomTaskTypePrerequisitesAdmin,
        CustomTaskTypeRequiredForAdmin,
    ]


class TaskHistoryCertificatePageAdmin(admin.StackedInline):
    model = TaskHistoryCertificatePage
    extra = 0


class TaskHistoryCertificateAdmin(admin.ModelAdmin):
    search_fields = (
        "task_history__employee__first_name",
        "task_history__employee__last_name",
    )
    model = TaskHistoryCertificate
    list_display = ("id", "created", "get_task_employee", "get_task_type")
    inlines = [TaskHistoryCertificatePageAdmin]
    list_filter = ("task_history__type__facility__state_facility",)
    raw_id_fields = ("task_history",)

    def get_task_employee(self, obj):
        return obj.task_history.employee

    get_task_employee.short_description = "Employee"

    def get_task_type(self, obj):
        return obj.task_history.type

    get_task_type.short_description = "Task type"


class TrainingEventAdmin(admin.ModelAdmin):
    raw_id_fields = ("training_for", "attendees", "employee_tasks")


class TaskHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "facility",
        "employee",
        "type",
        "completion_date",
        "expiration_date",
        "status",
        "credit_hours",
    )
    list_filter = (
        "employee__facility",
        "employee",
        "type",
        "completion_date",
        "expiration_date",
        "status",
        "credit_hours",
        "type__facility__state_facility",
    )
    raw_id_fields = ("employee", "type")

    def facility(self, obj):
        return obj.employee.facility

    facility.admin_order_field = "employee__facility"


class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "type",
        "due_date",
        "status",
    )
    list_filter = (
        "type",
        "due_date",
        "status",
        EmployeeFacilityListFilter,
        EmployeeListFilter,
        "type__facility__state_facility",
    )


class OutstandingTrainingsAdminInline(admin.StackedInline):
    model = Task
    readonly_fields = "type", "due_date", "schedule_date"
    fieldsets = ((None, {"fields": (("type", "due_date"), "schedule_date")}),)
    verbose_name = "Outstanding training"
    verbose_name_plural = "Outstanding trainings"
    extra = 0

    def get_queryset(self, request):
        qs = super(OutstandingTrainingsAdminInline, self).get_queryset(request)
        qs = qs.select_related("type")
        qs = qs.filter(type__is_training=True)
        qs = qs.order_by("-due_date")

        scheduled_events = TrainingEvent.objects.order_by("start_time")
        qs = qs.prefetch_related(Prefetch("training_events", queryset=scheduled_events))

        return qs

    def schedule_date(self, obj):
        training_events = list(obj.training_events.all())
        if training_events:
            event = training_events[0]
            return formats.date_format(event.start_time, "DATETIME_FORMAT")

    schedule_date.short_description = "Date scheduled to attend training"


class OutstandingTasksAdminInline(admin.StackedInline):
    model = Task
    readonly_fields = "type", "due_date"
    fieldsets = ((None, {"fields": (("type", "due_date"),)}),)
    verbose_name = "Outstanding task"
    verbose_name_plural = "Outstanding tasks"
    extra = 0

    def get_queryset(self, request):
        qs = super(OutstandingTasksAdminInline, self).get_queryset(request)
        qs = qs.select_related("type")
        qs = qs.filter(type__is_training=False)
        qs = qs.order_by("-due_date")

        return qs


class CompletedTrainingsAdminInline(admin.StackedInline):
    model = TaskHistory
    readonly_fields = "type", "completion_date", "next_due_date"
    fields = "type", "completion_date", "next_due_date"
    verbose_name = "Completed training"
    verbose_name_plural = "Completed trainings"
    extra = 0

    def get_queryset(self, request):
        qs = super(CompletedTrainingsAdminInline, self).get_queryset(request)
        qs = qs.select_related("type")
        qs = qs.filter(type__is_training=True)
        qs = qs.filter(status=TaskHistoryStatus.completed)
        qs = qs.order_by("completion_date")

        return qs

    def next_due_date(self, obj):
        return obj.expiration_date

    next_due_date.short_description = "Next due date"
    next_due_date.admin_order_field = "expiration_date"


class CompletedTasksAdminInline(admin.StackedInline):
    model = TaskHistory
    readonly_fields = "type", "completion_date", "next_due_date"
    fields = "type", "completion_date", "next_due_date"
    verbose_name = "Completed task"
    verbose_name_plural = "Completed tasks"
    extra = 0

    def get_queryset(self, request):
        qs = super(CompletedTasksAdminInline, self).get_queryset(request)
        qs = qs.select_related("type")
        qs = qs.filter(type__is_training=False)
        qs = qs.filter(status=TaskHistoryStatus.completed)
        qs = qs.order_by("completion_date")

        return qs

    def next_due_date(self, obj):
        return obj.expiration_date

    next_due_date.short_description = "Next due date"
    next_due_date.admin_order_field = "expiration_date"


class EmployeeAdmin(admin.ModelAdmin):
    change_list_template = "trainings/admin/trainings/employee/change_list.html"
    change_form_template = "trainings/admin/trainings/employee/change_form.html"
    list_display = (
        "first_name",
        "last_name",
        "facility",
        "all_positions",
        "all_responsibilities",
        "user",
    )
    search_fields = (
        "first_name",
        "last_name",
        "user__username",
        "user__email",
    )
    list_filter = (
        "facility",
        "positions",
        "other_responsibilities",
        "facility__state_facility",
    )
    fields = (
        "facility",
        "first_name",
        "last_name",
        "phone_number",
        "email",
        "ssn",
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
        "code_verified",
        "deactivation_date",
        "deactivation_note",
        "deactivation_reason",
        "is_active",
        "is_reactivated",
    )
    inlines = [
        OutstandingTrainingsAdminInline,
        OutstandingTasksAdminInline,
        CompletedTrainingsAdminInline,
        CompletedTasksAdminInline,
    ]

    def all_positions(self, obj):
        return ", ".join([objs.name for objs in obj.positions.all()])

    def all_responsibilities(self, obj):
        return ", ".join([objs.name for objs in obj.other_responsibilities.all()])

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = super(EmployeeAdmin, self).get_urls()
        my_urls = [
            re_path(
                r"^reapply-positions/$",
                self.reapply_positions_view,
                name="%s_%s_reapply_positions_all" % info,
            ),
            re_path(
                r"^reapply-responsibilities/$",
                self.reapply_responsibilities_view,
                name="%s_%s_reapply_responsibilities_all" % info,
            ),
            re_path(
                r"^(.+)/reapply-positions/$",
                self.reapply_positions_view,
                name="%s_%s_reapply_positions" % info,
            ),
            re_path(
                r"^(.+)/reapply-responsibilities/$",
                self.reapply_responsibilities_view,
                name="%s_%s_reapply_responsibilities" % info,
            ),
        ]
        return my_urls + urls

    def reapply_positions_view(self, request, object_id=None):
        if object_id:
            count = 1
        else:
            count = Employee.objects.count()
        reapply_employee_positions.delay(object_id)
        messages.success(request, "Reapplying positions for %s employees." % count)
        opts = self.model._meta
        url = reverse(
            "admin:{app}_{model}_changelist".format(
                app=opts.app_label,
                model=opts.model_name,
            )
        )
        return HttpResponseRedirect(url)

    def reapply_responsibilities_view(self, request, object_id=None):
        if object_id:
            count = 1
        else:
            count = Employee.objects.count()
        reapply_employee_responsibilities.delay(object_id)
        messages.success(request, "Reapplying responsibilities for %s employees." % count)
        opts = self.model._meta
        url = reverse(
            "admin:{app}_{model}_changelist".format(
                app=opts.app_label,
                model=opts.model_name,
            )
        )
        return HttpResponseRedirect(url)

    def change_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
        employee = self.model.objects.get(pk=object_id)
        summary = compute_compliance_for_employee(employee, datetime.date.today())

        compliance_list = []
        for compliance in summary["compliance_list"]:
            base_task_not_completed = compliance.get("base_task_not_completed", False)
            if not base_task_not_completed:
                compliance_list.append(compliance)

        extra_context["compliance_list"] = compliance_list

        return super().change_view(request, object_id, extra_context=extra_context)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == "facility":
            kwargs["queryset"] = Facility.objects.order_by("name")
        return super(EmployeeAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


class EmployeeInline(admin.StackedInline):
    model = Employee.other_responsibilities.through
    readonly_fields = ("employee",)
    extra = 0
    max_num = 10000

    def has_add_permission(self, request, obj=None):
        return False


class ResponsibilityAdmin(admin.ModelAdmin):
    model = Responsibility
    fields = ("name", "question", "question_position_restriction", "facility")
    list_filter = ("facility__state_facility",)
    inlines = [EmployeeInline]


class GlobalRequirementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "task_type",
    )
    list_filter = ("task_type__facility__state_facility",)
    fieldsets = ((None, {"fields": ("task_type",)}),)

    def save_model(self, request, obj, form, change):
        if change:
            apply_global_requirement(obj.pk)
        super().save_model(request, obj, form, change)


class SponsorStateAdmin(admin.ModelAdmin):
    model = SponsorState
    list_display = ("id", "state", "sponsor")


class StateAdmin(admin.ModelAdmin):
    model = State
    list_display = (
        "id",
        "get_state_display",
    )


class FacilityQuestionStateAdmin(admin.ModelAdmin):
    model = FacilityQuestionState


class PositionAdmin(admin.ModelAdmin):
    model = Position
    list_filter = ("responsibilities__facility__state_facility",)


admin.site.register(Antirequisite)
admin.site.register(Course, CourseAdmin)
admin.site.register(CourseItem, CourseItemAdmin)
admin.site.register(CourseItemMultiChoice, CourseItemOptionsAdmin)
admin.site.register(CustomTaskType, CustomTaskTypeAdmin)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(EmployeeCourse, EmployeeCourseAdmin)
admin.site.register(Facility, FacilityAdmin)
admin.site.register(FacilityQuestion, FacilityQuestionAdmin)
admin.site.register(FacilityQuestionRule, FacilityQuestionRuleAdmin)
admin.site.register(GlobalRequirement, GlobalRequirementAdmin)
admin.site.register(MultiChoiceOption, MultiChoiceOptionAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(PositionGroup)
admin.site.register(Responsibility, ResponsibilityAdmin)
admin.site.register(ResponsibilityEducationRequirement)
admin.site.register(Task, TaskAdmin)
admin.site.register(TaskHistory, TaskHistoryAdmin)
admin.site.register(TaskType, TaskTypeAdmin)
admin.site.register(TaskHistoryCertificate, TaskHistoryCertificateAdmin)
admin.site.register(TaskTypeEducationCredit)
admin.site.register(TrainingEvent, TrainingEventAdmin)
admin.site.register(Trainer, TrainerAdmin)
admin.site.register(SponsorState, SponsorStateAdmin)
admin.site.register(State, StateAdmin)
admin.site.register(FacilityQuestionState, FacilityQuestionStateAdmin)
