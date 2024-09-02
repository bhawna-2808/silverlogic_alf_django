import logging
import re
from datetime import date
from mimetypes import guess_type
from tempfile import NamedTemporaryFile

from django.core.files.base import File
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

from actstream import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, views
from rest_framework.decorators import action as action_decorator
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ReadOnlyModelViewSet, mixins

from apps.api.authentication import ApiKeyUrlAuthentication, TrainingsTimedAuthTokenAuthentication
from apps.api.filters import (
    CustomTaskTypeFilter,
    EmployeeFilter,
    TaskFilter,
    TaskHistoryFilter,
    TaskTypeFilter,
    TrainingEventFilter,
)
from apps.api.permissions import FacilityHasStaffSubscriptionIfRequired, IsSameFacilityForEditing
from apps.api.trainings.course_serializers import (
    CourseItemBooleanSerializer,
    CourseItemCreateSerializer,
    CourseItemLetterSizeImageSerializer,
    CourseItemMultiChoiceCreateSerializer,
    CourseItemMultiChoiceSerializer,
    CourseItemSerializer,
    CourseItemTextSerializer,
    CourseItemVideoSerializer,
    CourseOpenSerializer,
    CourseSerializer,
    EmployeeCourseItemSerializer,
    EmployeeCourseSerializer,
    MultiChoiceOptionSerializer,
)
from apps.api.views import generate_pdf
from apps.facilities.models import FacilityUser
from apps.trainings.continuing_education import (
    compute_compliance_for_employee,
    compute_compliance_for_facility,
)
from apps.trainings.models import (
    Course,
    CourseItem,
    CourseItemBoolean,
    CourseItemLetterSizeImage,
    CourseItemMultiChoice,
    CourseItemText,
    CourseItemVideo,
    CustomTaskType,
    Employee,
    EmployeeCourse,
    EmployeeCourseItem,
    Facility,
    Position,
    PositionGroup,
    Responsibility,
    ResponsibilityEducationRequirement,
    Task,
    TaskHistory,
    TaskHistoryCertificate,
    TaskHistoryStatus,
    TaskType,
    TaskTypeEducationCredit,
    TrainingEvent,
)
from apps.trainings.tasks import reapply_employee_responsibilities
from apps.trainings.utils import send_certificate_to_admins, send_custom_task_type_mail
from apps.utils.mixins import MultiSerializerMixin
from apps.utils.viewsets import ChildViewSetMixin

from ..facilities.permissions import NotManagerOrCanAccessStaff
from ..facilities.serializers import FacilitySerializer
from ..permissions import IsExternalClient, IsRole, NonEmployeeUserEditing
from ..users.serializers import UserSerializer
from ..views import PdfParametersView, PdfView
from .filters import CourseFilter
from .serializers import (
    CustomTaskTypeReadSerializer,
    CustomTaskTypeWriteSerializer,
    DefaultPositionSerializer,
    DefaultTaskTypeEducationCreditSerializer,
    EmployeeCloudCareSerializer,
    EmployeeCreateSerializer,
    EmployeeEditSerializer,
    EmployeeInviteSerializer,
    EmployeeReadExpandableSerializer,
    EmployeeReadSerializer,
    PositionCloudCareSerializer,
    PositionGroupReadSerializer,
    PositionSerializer,
    ResponsibilityEducationRequirementReadSerializer,
    ResponsibilityEducationRequirementWriteSerializer,
    ResponsibilityReadWriteSerializer,
    TaskHistoryCertificatePage,
    TaskHistoryCertificateSerializer,
    TaskHistoryCreateSerializer,
    TaskHistoryExpandedSerializer,
    TaskHistoryReadSerializer,
    TaskReadExpandSerializer,
    TaskReadSerializer,
    TaskTypeReadSerializer,
    TaskTypeSimpleSerializer,
    TaskTypeWriteSerializer,
    TaskWriteSerializer,
    TrainingEventReadSerializer,
    TrainingEventWriteSerializer,
)

logger = logging.getLogger(__name__)


def get_response_format(params, data):
    responseFormat = params.get("object")
    if responseFormat == "true":
        return Response({"count": len(data), "results": data})

    return Response(data)


def _generate_course_certificate_page(template_name, context, certificate):
    with NamedTemporaryFile(suffix=".pdf") as file:
        generate_pdf(template_name, file, context)
        return TaskHistoryCertificatePage.objects.create(certificate=certificate, page=File(file))


def generate_course_certificate(employee, facility, task_history, employee_course):
    certificate = TaskHistoryCertificate.objects.create(task_history=task_history)
    task_name = employee_course.course.name
    context = {
        "employee": employee,
        "course": employee_course.course,
        "facility": facility,
        "completed_date": employee_course.completed_date,
        "task_name": task_name,
        "admin_signature": facility.admin_signature.url if facility.admin_signature else "",
    }
    pages = [
        _generate_course_certificate_page(
            "trainings/completed-certificate.pdf.html", context, certificate
        ),
        _generate_course_certificate_page(
            "trainings/completed-certificate-back.pdf.html", context, certificate
        ),
    ]
    if employee_course.signature:
        context["signature"] = employee_course.signature.url
        pages.append(
            _generate_course_certificate_page(
                "trainings/completed-certificate-signature.pdf.html",
                context,
                certificate,
            )
        )
    send_certificate_to_admins(employee, task_name, facility, pages)


class EmployeeViewSet(MultiSerializerMixin, ModelViewSet):
    serializers = {
        "POST": EmployeeCreateSerializer,
        "PUT": EmployeeEditSerializer,
        "PATCH": EmployeeEditSerializer,
        "GET": EmployeeReadSerializer,
    }
    queryset = (
        Employee.objects.all()
        .select_related("facility")
        .prefetch_related(
            "positions",
            "positions__responsibilities",
            "other_responsibilities",
            "other_responsibilities__position_set",
        )
    )
    permission_classes = (
        IsAuthenticated,
        IsSameFacilityForEditing,
        IsRole(FacilityUser.Role.account_admin, FacilityUser.Role.manager),
        FacilityHasStaffSubscriptionIfRequired,
        NotManagerOrCanAccessStaff,
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = EmployeeFilter

    def get_queryset(self):
        qs = super(EmployeeViewSet, self).get_queryset().filter(facility=self.request.facility)
        return qs

    def perform_create(self, serializer):
        instance = serializer.save()
        action.send(
            self.request.user,
            verb="created employee",
            action_object=instance,
            target=instance.facility,
        )

    @action_decorator(methods=["get"], permission_classes=(IsAuthenticated,), detail=False)
    def me(self, request):
        user = request.user
        employee = Employee.objects.filter(user=user).first()
        serializer = EmployeeReadExpandableSerializer(
            instance=employee, context={"request": request}
        )
        return Response(serializer.data)

    @action_decorator(
        methods=["post"],
        permission_classes=(IsAuthenticated, NotManagerOrCanAccessStaff),
        serializers={"POST": EmployeeInviteSerializer},
        detail=False,
    )
    def invite(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data)


class CloudCareEmployeeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):

    queryset = Employee.objects.all()
    serializer_class = EmployeeCloudCareSerializer
    permission_classes = [IsExternalClient]


class CloudCarePositionViewSet(mixins.ListModelMixin, GenericViewSet):

    queryset = Position.objects.all()
    serializer_class = PositionCloudCareSerializer
    permission_classes = [IsExternalClient]


class EmployeesListPdfView(PdfView):
    queryset = Employee.objects.all()
    template_name = "trainings/employee-list.pdf.html"
    filename = "Employee List.pdf"

    def get_employees(self):
        employees = self.get_queryset()
        employee_ids = self.get_employee_ids()
        employees = sorted(employees, key=lambda r: employee_ids.index(r.pk))
        return employees

    def get_queryset(self):
        queryset = super(EmployeesListPdfView, self).get_queryset()
        queryset = queryset.filter(facility=self.request.facility)
        queryset = queryset.filter(pk__in=self.get_employee_ids())
        return queryset

    def get_employee_ids(self):
        employee_ids_param = self.request.query_params.get("employee_ids", "")
        if not re.match(r"^\d[\d,]*$", employee_ids_param):
            return []
        return list(map(int, employee_ids_param.split(",")))

    def get_context_data(self, **kwargs):
        context = super(EmployeesListPdfView, self).get_context_data(**kwargs)
        context["employees"] = self.get_employees()
        return context


class EmployeesDetailPdfView(PdfView):
    queryset = Employee.objects.all()
    template_name = "trainings/employee-detail.pdf.html"

    def get_queryset(self):
        queryset = super(EmployeesDetailPdfView, self).get_queryset()
        queryset = queryset.filter(facility=self.request.facility)
        return queryset

    def get_context_data(self, **kwargs):
        employee = self.get_object()
        context = super(EmployeesDetailPdfView, self).get_context_data(**kwargs)
        context["employee"] = employee
        context["outstanding_tasks"] = employee.trainings_task_set.filter(
            type__is_training=False
        ).outstanding()
        context["outstanding_trainings"] = employee.trainings_task_set.filter(
            type__is_training=True
        ).outstanding()
        context["completed_tasks"] = employee.trainings_taskhistory_set.filter(
            type__is_training=False, status=TaskHistoryStatus.completed
        )
        context["completed_trainings"] = employee.trainings_taskhistory_set.filter(
            type__is_training=True, status=TaskHistoryStatus.completed
        )
        return context

    def get_filename(self):
        return "{}.pdf".format(self.get_object())


class EmployeesCertificatesPdfView(PdfView):
    queryset = Employee.objects.all()
    template_name = "trainings/employee-certificates.pdf.html"

    def get_queryset(self):
        queryset = super(EmployeesCertificatesPdfView, self).get_queryset()
        queryset = queryset.filter(facility=self.request.facility)
        return queryset

    def get_context_data(self, **kwargs):
        employee = self.get_object()
        context = super(EmployeesCertificatesPdfView, self).get_context_data(**kwargs)
        context["employee"] = employee
        context["completed_tasks"] = employee.trainings_taskhistory_set.filter(
            type__is_training=False, status=TaskHistoryStatus.completed
        )
        context["completed_trainings"] = employee.trainings_taskhistory_set.filter(
            type__is_training=True, status=TaskHistoryStatus.completed
        )
        return context

    def get_filename(self):
        return "{}-certificates.pdf".format(self.get_object())


class UpcomingTasksPdfView(PdfParametersView):
    queryset = Task.objects.all()
    template_name = "trainings/upcoming-tasks.pdf.html"

    def get_tasks(self, params):
        tasks = self.get_queryset(params)
        task_ids = self.get_task_ids(params)
        tasks = sorted(tasks, key=lambda r: task_ids.index(r.pk))
        return tasks

    def get_queryset(self, params):
        queryset = super(UpcomingTasksPdfView, self).get_queryset()
        queryset = queryset.filter(pk__in=self.get_task_ids(params))
        return queryset

    def get_task_ids(self, params):
        task_ids_param = params.get("task_ids", "")
        if not re.match(r"^\d[\d,]*$", task_ids_param):
            return []
        return list(map(int, task_ids_param.split(",")))

    def get_type(self, params):
        return params.get("type", "")

    def get_context_data(self, **kwargs):
        parameters = self.get_parameters()
        context = super(UpcomingTasksPdfView, self).get_context_data(**kwargs)
        context["type"] = self.get_type(parameters)
        context["tasks"] = self.get_tasks(parameters)
        return context

    def get_filename(self):
        parameters = self.get_parameters()
        return "Upcoming {}s.pdf".format(self.get_type(parameters))


class ResponsibilityViewSet(ModelViewSet):
    queryset = Responsibility.objects.all()
    serializer_class = ResponsibilityReadWriteSerializer
    permission_classes = IsAuthenticated, IsSameFacilityForEditing

    def get_queryset(self):
        queryset = super(ResponsibilityViewSet, self).get_queryset()

        # Only filter in the GET because if you filter on all requests and then
        # try to update a responsibility that you don't have access to, instead
        # of being denied, you will create a new responsibility. Seems like a
        # bug with DRF.  Remove the if statement and run tests to see.
        if self.request.method == "GET":
            facility = self.request.facility
            return queryset.filter(Q(facility=facility) | Q(facility=None))
        return queryset

    # Handle the setting of permissions here instead of the serializer because
    # I was unable to have the serializer work.  Regular M2M fields seemed to
    # work fine but the reverse M2M did not.
    def perform_create(self, serializer):
        responsibility = serializer.save()
        if isinstance(self.request.data.get("positions"), list):
            responsibility.position_set.set(self.request.data["positions"])
            responsibility.save()

    def perform_update(self, serializer):
        responsibility = serializer.save()
        if isinstance(self.request.data.get("positions"), list):
            responsibility.position_set.set(self.request.data["positions"])
            responsibility.save()


class ResponsibilityEducationRequirementViewSet(MultiSerializerMixin, ModelViewSet):
    serializers = {
        "POST": ResponsibilityEducationRequirementWriteSerializer,
        "PUT": ResponsibilityEducationRequirementWriteSerializer,
        "PATCH": ResponsibilityEducationRequirementWriteSerializer,
        "GET": ResponsibilityEducationRequirementReadSerializer,
    }
    queryset = ResponsibilityEducationRequirement.objects.all()
    permission_classes = (IsAuthenticated,)


class PositionViewSet(MultiSerializerMixin, ModelViewSet):
    serializers = {
        "POST": DefaultPositionSerializer,
        "PUT": DefaultPositionSerializer,
        "PATCH": DefaultPositionSerializer,
    }
    queryset = Position.objects.prefetch_related("responsibilities")
    permission_classes = (
        IsAuthenticated,
        IsSameFacilityForEditing,
        FacilityHasStaffSubscriptionIfRequired,
    )
    serializer_class = PositionSerializer


class TaskTypeViewSet(MultiSerializerMixin, ModelViewSet):
    serializers = {
        "POST": TaskTypeWriteSerializer,
        "PUT": TaskTypeWriteSerializer,
        "PATCH": TaskTypeWriteSerializer,
        "GET": TaskTypeReadSerializer,
    }
    queryset = TaskType.objects.all()
    permission_classes = (
        IsAuthenticated,
        IsSameFacilityForEditing,
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TaskTypeFilter

    def get_queryset(self):
        facility = self.request.facility
        queryset = super(TaskTypeViewSet, self).get_queryset()
        return queryset.filter(Q(facility=facility) | Q(facility=None))


class CustomTaskTypeViewSet(
    MultiSerializerMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializers = {
        "POST": CustomTaskTypeWriteSerializer,
        "GET": CustomTaskTypeReadSerializer,
    }
    queryset = CustomTaskType.objects.all()
    permission_classes = (
        IsAuthenticated,
        IsSameFacilityForEditing,
        FacilityHasStaffSubscriptionIfRequired,
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CustomTaskTypeFilter

    def get_queryset(self):
        facility = self.request.facility
        queryset = super(CustomTaskTypeViewSet, self).get_queryset()
        return queryset.filter(Q(facility=facility) | Q(facility=None))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset().filter(is_request=False))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action_decorator(methods=["post"], detail=False)
    def request(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        custom_task_type = serializer.save()
        admin_url = request.build_absolute_uri(
            reverse("admin:trainings_customtasktype_change", args=(custom_task_type.id,))
        )
        send_custom_task_type_mail(custom_task_type, admin_url)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TaskViewSet(MultiSerializerMixin, ModelViewSet):
    serializers = {
        "POST": TaskWriteSerializer,
        "PUT": TaskWriteSerializer,
        "PATCH": TaskWriteSerializer,
        "GET": TaskReadSerializer,
    }
    queryset = Task.objects.all()
    permission_classes = (IsAuthenticated, FacilityHasStaffSubscriptionIfRequired)
    serializer_class = TaskReadSerializer
    filter_backends = filters.OrderingFilter, DjangoFilterBackend
    filterset_class = TaskFilter

    def get_queryset(self):
        queryset = super(TaskViewSet, self).get_queryset()

        user = self.request.user
        if user.facility_users.role == FacilityUser.Role.trainings_user or (
            user.facility_users.role == FacilityUser.Role.manager
            and not user.facility_users.can_see_staff
        ):
            if getattr(user, "employee", None):
                queryset = queryset.filter(employee=user.employee)
            else:
                logger.exception("User is not linked to an employee")
                return
        return queryset.filter(employee__is_active=True, employee__facility=self.request.facility)

    @action_decorator(
        methods=["get"],
        permission_classes=(IsAuthenticated,),
        serializers={"GET": TaskReadExpandSerializer},
        detail=False,
        filter_backends=(filters.OrderingFilter, DjangoFilterBackend),
        filterset_class=TaskFilter,
    )
    def me(self, request):
        employee = request.user.employee
        tasks = Task.objects.filter(
            employee=employee,
        )

        language = self.request.query_params.get("type__course__language", None)
        if language:
            serializers = self.get_serializer(
                instance=tasks.filter(Q(type__course__language=language) | Q(type__course=None)),
                many=True,
            )
        else:
            serializers = self.get_serializer(instance=tasks, many=True)

        return get_response_format(request.query_params, serializers.data)


class TaskHistoryViewSet(MultiSerializerMixin, ModelViewSet):
    serializers = {
        "POST": TaskHistoryCreateSerializer,
        "PUT": TaskHistoryCreateSerializer,
        "PATCH": TaskHistoryCreateSerializer,
        "GET": TaskHistoryReadSerializer,
    }
    queryset = TaskHistory.objects.all()
    permission_classes = (IsAuthenticated, FacilityHasStaffSubscriptionIfRequired)
    serializer_class = TaskHistoryReadSerializer
    filter_backends = filters.OrderingFilter, DjangoFilterBackend
    filterset_class = TaskHistoryFilter

    def get_queryset(self):
        queryset = super(TaskHistoryViewSet, self).get_queryset()

        return queryset.filter(employee__is_active=True, employee__facility=self.request.facility)

    @action_decorator(
        methods=["get"],
        permission_classes=(IsAuthenticated,),
        serializers={"GET": TaskHistoryExpandedSerializer},
        detail=False,
    )
    def me(self, request):
        employee = request.user.employee
        tasks_history = TaskHistory.objects.filter(
            employee=employee,
        )
        serializers = self.get_serializer(instance=tasks_history, many=True)
        return get_response_format(request.query_params, serializers.data)

    @action_decorator(
        methods=["get", "delete", "post"],
        detail=True,
        authentication_classes=(
            TrainingsTimedAuthTokenAuthentication,
            ApiKeyUrlAuthentication,
        ),
    )
    def certificate(self, request, pk=None):
        task_history = self.get_object()
        try:
            certificate = task_history.certificate
        except TaskHistoryCertificate.DoesNotExist:
            certificate = None

        if request.method == "DELETE":
            if certificate:
                certificate.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        elif request.method == "POST":
            serializer = TaskHistoryCertificateSerializer(
                instance=certificate,
                data=request.data,
                context={"task_history": task_history},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        else:
            if certificate:
                certificate_page_index = int(request.GET.get("page", 0))
                try:
                    certificate_page = certificate.pages.all().order_by("id")[
                        certificate_page_index
                    ]
                except IndexError:
                    return HttpResponse(status=status.HTTP_404_NOT_FOUND)
            else:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)

            content_type, _ = guess_type(certificate_page.page.name)
            extension = certificate_page.page.name.split(".")[-1]

            response = HttpResponse(certificate_page.page.read(), content_type=content_type)
            response["Content-Disposition"] = 'filename="{} - Certificate - Page {}.{}"'.format(
                task_history.type, certificate_page_index + 1, extension
            )
            return response


class TrainingEventViewSet(MultiSerializerMixin, ModelViewSet):
    serializers = {
        "POST": TrainingEventWriteSerializer,
        "PUT": TrainingEventWriteSerializer,
        "PATCH": TrainingEventWriteSerializer,
        "GET": TrainingEventReadSerializer,
    }
    queryset = TrainingEvent.objects.all()
    filter_backends = filters.OrderingFilter, DjangoFilterBackend
    filterset_class = TrainingEventFilter
    permission_classes = (IsAuthenticated, FacilityHasStaffSubscriptionIfRequired)

    def get_queryset(self):
        """
        Optionally restricts the returned TrainingEvents to ones a certain user attended
        """
        queryset = super(TrainingEventViewSet, self).get_queryset()
        queryset = queryset.filter(facility=self.request.facility)

        attendee = self.request.query_params.get("attendee", None)
        if attendee is not None:
            queryset = queryset.filter(attendees__in=attendee)

        return queryset

    @action_decorator(methods=["post"], detail=True)
    def finish(self, request, pk=None):
        incomplete_attendee_ids = request.data.get("incomplete_attendees", [])
        credit_hours = float(request.data.get("credit_hours", 0))
        training_event = self.get_object()
        training_event.finish(incomplete_attendee_ids, credit_hours)
        return Response({"status": "TrainingEvent completed"})


class TaskTypeEducationCreditViewSet(MultiSerializerMixin, ModelViewSet):
    queryset = TaskTypeEducationCredit.objects.all()
    serializer_class = DefaultTaskTypeEducationCreditSerializer

    def get_queryset(self):
        queryset = super(TaskTypeEducationCreditViewSet, self).get_queryset()
        facility = self.request.facility
        global_credits = Q(facility=None) & Q(tasktype__facility=None)
        owned_credits = Q(facility=facility)
        queryset = queryset.filter(global_credits | owned_credits)

        return queryset


class ComplianceView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        facility = self.request.facility

        qs = Task.objects.filter(employee__facility=facility, employee__is_active=True)

        count = qs.count()
        compliance = {
            "facility": {
                "compliance_percent": 0
                if count == 0
                else 100.0 * qs.filter(due_date__gte=timezone.now().date()).count() / qs.count()
            }
        }

        return Response(compliance)


class CurrentUserView(views.APIView):
    def get(self, request, format=None):
        user = request.user
        if user.is_anonymous:
            return Response({"anon": "not logged in"})
        return Response(
            {
                "user": UserSerializer(user, context={"request": request}).data,
                "facility": FacilitySerializer(request.facility).data,
            }
        )


class TrainingEventPdfView(PdfView):
    template_name = "trainings/training-event.pdf.html"
    queryset = TrainingEvent.objects.all()

    def get_queryset(self):
        queryset = super(TrainingEventPdfView, self).get_queryset()
        queryset = queryset.filter(facility=self.request.facility)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(TrainingEventPdfView, self).get_context_data(**kwargs)
        context["object"] = self.get_object()
        return context

    def get_filename(self):
        return "{} Event.pdf".format(self.get_object().training_for.name)


class AllowedTaskTypesViewSet(ChildViewSetMixin, ReadOnlyModelViewSet):
    parent_viewset = EmployeeViewSet
    queryset = TaskType.objects.all()
    serializer_class = TaskTypeSimpleSerializer
    permission_classes = (
        IsAuthenticated,
        IsSameFacilityForEditing,
        FacilityHasStaffSubscriptionIfRequired,
    )

    def get_queryset(self):
        return self.parent_object.get_tasktypes_allowed_by_prerequisites()


class ContinuingEducationSummaryForFacilityView(views.APIView):
    def get(self, request, facility_id):
        user = self.request.user
        facility_qs = Facility.objects.filter(pk=facility_id)
        if not facility_qs.count():
            return Response(
                {"errors": ["Facility with id {} not found".format(facility_id)]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        facility = facility_qs.first()
        summary = compute_compliance_for_facility(facility, date.today(), user)
        return Response({"facility_summary": summary, "pk": facility_id})


class ContinuingEducationSummaryForEmployeeView(views.APIView):
    def get(self, request, employee_id):
        employee_qs = Employee.objects.filter(pk=employee_id)
        if not employee_qs.count():
            return Response(
                {"errors": ["Employee with id {} not found".format(employee_id)]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        employee = employee_qs.first()
        summary = compute_compliance_for_employee(employee, date.today())
        return Response({"employee_summary": summary, "pk": employee_id})


class PositionGroupViewSet(MultiSerializerMixin, ModelViewSet):
    queryset = PositionGroup.objects.all()
    serializer_class = PositionGroupReadSerializer
    permission_classes = (IsAuthenticated, FacilityHasStaffSubscriptionIfRequired)


class CourseViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = CourseSerializer
    queryset = Course.objects.all()
    permission_classes = (IsAuthenticated, NonEmployeeUserEditing)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CourseFilter

    def get_queryset(self):
        queryset = super(CourseViewSet, self).get_queryset()
        published = self.request.query_params.get("published")
        if published:
            queryset = queryset.filter(published=True if published == "true" else False)

        user = self.request.user
        if user.facility_users.role == FacilityUser.Role.trainings_user:
            queryset = queryset.filter(published=True)

        return queryset

    @action_decorator(
        methods=["get"],
        serializer_class=CourseOpenSerializer,
        authentication_classes=(TrainingsTimedAuthTokenAuthentication,),
        permission_classes=(IsAuthenticated,),
        detail=True,
    )
    def open(self, request, *args, **kwargs):
        course = self.get_object()
        serializer = self.get_serializer(instance=course, context={"request": request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        response = super(CourseViewSet, self).list(request, args, kwargs)
        return get_response_format(request.query_params, response.data)

    @action_decorator(methods=["get", "post"], serializer_class=CourseItemSerializer, detail=True)
    def items(self, request, pk):
        course = self.get_object()
        if request.method == "POST":
            serializer = CourseItemCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.course = course
            item = serializer.save()
            response_serializer = self.get_serializer(instance=item)
            return Response(data=response_serializer.data, status=status.HTTP_201_CREATED)

        serializer = self.get_serializer(instance=course.items.all(), many=True)
        return get_response_format(request.query_params, serializer.data)

    @action_decorator(
        methods=["post"],
        serializer_class=EmployeeCourseSerializer,
        authentication_classes=(TrainingsTimedAuthTokenAuthentication,),
        permission_classes=(IsAuthenticated,),
        detail=True,
    )
    def complete(self, request, pk):
        course = self.get_object()
        employee = request.user.employee
        employee_items = EmployeeCourseItem.objects.filter(
            course_item__course=course, employee=employee
        )
        score = employee_items.filter(is_correct=True).count()
        employee_items.delete()

        # temporary check for mobile scoring, should be removed in the future when mobile is updated
        if request.data.get("score"):
            score = request.data.get("score")

        serializer = EmployeeCourseSerializer(
            data=request.data,
            context={
                "request": request,
                "course": self.get_object(),
                "status": EmployeeCourse.STATUSES.completed,
                "score": score,
            },
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        task = course.task_type.task_set.filter(employee=employee).first()

        #  TODO: how do we calculate credit_hour
        if task and instance.score >= course.minimum_score:
            task_history = task.complete(instance.completed_date)
            generate_course_certificate(employee, self.request.facility, task_history, instance)
            reapply_employee_responsibilities.delay(employee.id)

        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @action_decorator(
        methods=["post"],
        serializer_class=EmployeeCourseSerializer,
        permission_classes=(IsAuthenticated,),
        detail=True,
    )
    def start(self, request, pk):
        serializer = EmployeeCourseSerializer(
            data=request.data,
            context={
                "request": request,
                "course": self.get_object(),
                "status": EmployeeCourse.STATUSES.in_progress,
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @action_decorator(methods=["post"], permission_classes=(IsAuthenticated,), detail=True)
    def reset(self, request, pk):
        employee = request.user.employee
        course = self.get_object()
        EmployeeCourseItem.objects.filter(course_item__course=course, employee=employee).delete()
        EmployeeCourse.objects.filter(course=course, employee=employee).delete()
        serializer = self.get_serializer(instance=course)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class CourseItemViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = CourseItemSerializer
    queryset = CourseItem.objects.all()
    permission_classes = (IsAuthenticated, NonEmployeeUserEditing)

    def get_queryset(self):
        queryset = CourseItem.objects.all()
        published = self.request.query_params.get("published")
        course = self.request.query_params.get("course")
        publish_filter = None
        if published:
            publish_filter = True if published == "true" else False

        user = self.request.user
        if user.facility_users.role == FacilityUser.Role.trainings_user or published:
            publish_filter = True

        if publish_filter:
            queryset = queryset.filter(course__published=publish_filter)

        if course:
            queryset = queryset.filter(course=course)

        return queryset

    @action_decorator(methods=["get", "post"], detail=True)
    def texts(self, request, pk):
        item = self.get_object()
        if request.method == "POST":
            serializer = CourseItemTextSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(item=item)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

        serializer = CourseItemTextSerializer(instance=item.texts.all(), many=True)
        return get_response_format(request.query_params, serializer.data)

    @action_decorator(methods=["get", "post"], detail=True)
    def videos(self, request, pk):
        item = self.get_object()
        if request.method == "POST":
            serializer = CourseItemVideoSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(item=item)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

        serializer = CourseItemVideoSerializer(instance=item.videos.all(), many=True)
        return get_response_format(request.query_params, serializer.data)

    @action_decorator(methods=["get", "post"], detail=True)
    def letter_size_image(self, request, pk):
        item = self.get_object()
        if request.method == "POST":
            serializer = CourseItemLetterSizeImageSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(item=item)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

        serializer = CourseItemLetterSizeImageSerializer(
            instance=item.letter_size_image.all(), many=True
        )
        return get_response_format(request.query_params, serializer.data)

    @action_decorator(methods=["get", "post"], detail=True)
    def boolean(self, request, pk):
        item = self.get_object()
        if request.method == "POST":
            serializer = CourseItemBooleanSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(item=item)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

        serializer = CourseItemBooleanSerializer(instance=item.boolean.all(), many=True)
        return get_response_format(request.query_params, serializer.data)

    @action_decorator(
        methods=["get", "post"],
        serializer_class=CourseItemMultiChoiceSerializer,
        detail=True,
    )
    def choices(self, request, pk):
        item = self.get_object()
        if request.method == "POST":
            serializer = CourseItemMultiChoiceCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            option = serializer.save(item=item)
            response_serializer = CourseItemMultiChoiceSerializer(instance=option)
            return Response(data=response_serializer.data, status=status.HTTP_201_CREATED)

        serializer = self.get_serializer(instance=item.choices.all(), many=True)
        return get_response_format(request.query_params, serializer.data)

    @action_decorator(
        methods=["post"],
        permission_classes=(IsAuthenticated,),
        authentication_classes=(TrainingsTimedAuthTokenAuthentication,),
        detail=True,
    )
    def item_complete(self, request, pk):
        course_item = self.get_object()
        employee_course_item = EmployeeCourseItem.objects.filter(
            employee=request.user.employee, course_item=course_item
        ).first()
        if not employee_course_item:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"error": "Employee hasn't started this course item"},
            )
        serializer = EmployeeCourseItemSerializer(
            instance=employee_course_item,
            data=request.data,
            context={"request": request, "course_item": course_item},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        extra_data = {
            "total": course_item.course.items.filter(
                Q(boolean__isnull=False) | Q(choices__isnull=False)
            ).count(),
            "score": EmployeeCourseItem.objects.filter(
                course_item__course=course_item.course,
                employee=request.user.employee,
                is_correct=True,
            ).count(),
        }
        return Response(data={**serializer.data, **extra_data}, status=status.HTTP_200_OK)

    @action_decorator(
        methods=["post"],
        serializer_class=EmployeeCourseItemSerializer,
        authentication_classes=(TrainingsTimedAuthTokenAuthentication,),
        permission_classes=(IsAuthenticated,),
        detail=True,
    )
    def start(self, request, pk):
        course_item = self.get_object()
        serializer = EmployeeCourseItemSerializer(
            data=request.data, context={"request": request, "course_item": course_item}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


def filter_result(queryset, request):
    published = request.query_params.get("published", None)
    item = request.query_params.get("item", None)
    user = request.user
    if item:
        queryset = queryset.filter(item=item)

    publish_filter = None
    if published:
        publish_filter = True if published == "true" else False

    if user.facility_users.role == FacilityUser.Role.trainings_user:
        publish_filter = True

    if publish_filter:
        queryset = queryset.filter(item__course__published=publish_filter)

    return queryset


class CourseItemTextViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = CourseItemTextSerializer
    queryset = CourseItemText.objects.all()
    permission_classes = (IsAuthenticated, NonEmployeeUserEditing)

    def get_queryset(self):
        queryset = CourseItemText.objects.all()
        return filter_result(queryset, self.request)

    def list(self, request, *args, **kwargs):
        response = super(CourseItemTextViewSet, self).list(request, args, kwargs)
        return get_response_format(request.query_params, response.data)


class CourseItemBooleanViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = CourseItemBooleanSerializer
    queryset = CourseItemBoolean.objects.all()
    permission_classes = (IsAuthenticated, NonEmployeeUserEditing)

    def get_queryset(self):
        queryset = CourseItemBoolean.objects.all()
        return filter_result(queryset, self.request)

    def list(self, request, *args, **kwargs):
        response = super(CourseItemBooleanViewSet, self).list(request, args, kwargs)
        return get_response_format(request.query_params, response.data)


class CourseItemVideoViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = CourseItemVideoSerializer
    queryset = CourseItemVideo.objects.all()
    permission_classes = (IsAuthenticated, NonEmployeeUserEditing)

    def get_queryset(self):
        queryset = CourseItemVideo.objects.all()
        return filter_result(queryset, self.request)

    def list(self, request, *args, **kwargs):
        response = super(CourseItemVideoViewSet, self).list(request, args, kwargs)
        return get_response_format(request.query_params, response.data)


class CourseItemLetterSizeImageViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = CourseItemLetterSizeImageSerializer
    queryset = CourseItemLetterSizeImage.objects.all()
    permission_classes = (IsAuthenticated, NonEmployeeUserEditing)

    def get_queryset(self):
        queryset = CourseItemLetterSizeImage.objects.all()
        return filter_result(queryset, self.request)

    def list(self, request, *args, **kwargs):
        response = super(CourseItemLetterSizeImageViewSet, self).list(request, args, kwargs)
        return get_response_format(request.query_params, response.data)


class CourseItemMultiChoiceViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = CourseItemMultiChoiceSerializer
    queryset = CourseItemMultiChoice.objects.all()
    permission_classes = (IsAuthenticated, NonEmployeeUserEditing)

    def get_queryset(self):
        queryset = CourseItemMultiChoice.objects.all()
        return filter_result(queryset, self.request)

    def list(self, request, *args, **kwargs):
        response = super(CourseItemMultiChoiceViewSet, self).list(request, args, kwargs)
        return get_response_format(request.query_params, response.data)

    @action_decorator(methods=["get", "post"], detail=True)
    def options(self, request, pk):
        multi_choice = self.get_object()
        if request.method == "POST":
            serializer = MultiChoiceOptionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            option = serializer.save()
            multi_choice.options.add(option)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

        serializer = MultiChoiceOptionSerializer(instance=multi_choice.options.all(), many=True)
        return get_response_format(request.query_params, serializer.data)

    @action_decorator(methods=["get", "post"], detail=True)
    def answers(self, request, pk):
        multi_choice = self.get_object()
        if request.method == "POST":
            serializer = MultiChoiceOptionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            exists = multi_choice.options.filter(label=serializer.data.get("label")).first()
            if not exists:
                option = serializer.save()
                multi_choice.answers.add(option)
                return Response(data=serializer.data, status=status.HTTP_201_CREATED)

            multi_choice.answers.add(exists)
            serializer = MultiChoiceOptionSerializer(instance=exists)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

        serializer = MultiChoiceOptionSerializer(instance=multi_choice.answers.all(), many=True)
        return get_response_format(request.query_params, serializer.data)
