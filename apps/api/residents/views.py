import re

from django.db.models import Prefetch
from django.http import HttpResponse

from actstream import action as actstream_action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, response, status, viewsets
from rest_framework.response import Response
from timed_auth_token.authentication import TimedAuthTokenAuthentication

from apps.api.authentication import ApiKeyUrlAuthentication
from apps.api.decorators import action
from apps.examiners.models import ExaminationRequest, Examiner, ResidentAccess
from apps.facilities.models import FacilityUser, UserInviteResidentAccess, UserResidentAccess
from apps.residents.models import Archived1823, Resident, ResidentBedHold
from apps.residents.pdf import ResidentListPdfBuilder
from apps.residents.validations import should_examiner_signature_be_deleted
from apps.utils.viewsets import ChildViewSetMixin

from ..facilities.permissions import NotManagerOrCanAccessResidents
from ..mixins import DestroyModelMixin
from ..permissions import (
    FacilityHasResidentSubscription,
    IsAuthenticated,
    IsExternalClient,
    IsRoleFor,
    IsSameFacilityForEditing,
)
from ..views import PdfView, merge_pdfs
from .filters import ResidentFilter
from .serializers import (
    Archived1823Serializer,
    ExaminerAccessSerializer,
    ResidentBedHoldSerializer,
    ResidentCloudCareSerializer,
    ResidentSerializer,
)


class ResidentsViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Resident.objects.all().prefetch_related(
        "medications",
        "services_offered",
        "examination_requests",
        Prefetch(
            "examiners",
            queryset=ResidentAccess.objects.all().select_related("examiner__user"),
        ),
        Prefetch(
            "user_invites",
            queryset=UserInviteResidentAccess.objects.all().select_related("invite"),
        ),
    )
    serializer_class = ResidentSerializer
    permission_classes = [
        IsAuthenticated,
        IsRoleFor(
            FacilityUser.Role.account_admin,
            FacilityUser.Role.manager,
            methods=["POST", "DELETE"],
        ),
        IsRoleFor(
            FacilityUser.Role.account_admin,
            FacilityUser.Role.manager,
            FacilityUser.Role.examiner,
            methods=["GET", "PATCH", "PUT"],
        ),
        IsSameFacilityForEditing,
        FacilityHasResidentSubscription,
        NotManagerOrCanAccessResidents,
    ]
    filter_backends = (
        filters.OrderingFilter,
        DjangoFilterBackend,
    )
    filterset_class = ResidentFilter
    ordering_fields = ("last_name",)

    def perform_create(self, serializer):
        instance = serializer.save()
        actstream_action.send(
            self.request.user,
            verb="created resident",
            action_object=instance,
            target=instance.facility,
        )

    def get_queryset(self):
        queryset = super(ResidentsViewSet, self).get_queryset()
        queryset = queryset.filter(facility=self.request.facility)

        if self.request.role == FacilityUser.Role.examiner:
            queryset = queryset.filter(examiners__examiner=self.request.user.examiner)

        if self.request.role == FacilityUser.Role.manager:
            facility_user = self.request.user.facility_users
            qs_not_allowed_residents = UserResidentAccess.objects.filter(
                user=facility_user, is_allowed=False
            ).values("resident__id")
            queryset = queryset.exclude(pk__in=qs_not_allowed_residents)

        return queryset

    @action(methods=["POST"], permission_classes=[IsAuthenticated], detail=True)
    def will_delete_examiner_signature(self, request, pk=None):
        resident = self.get_object()
        will_delete = should_examiner_signature_be_deleted(resident, request.data)
        return Response({"result": will_delete})

    @action(methods=["GET", "POST"], serializer_class=ExaminerAccessSerializer, detail=True)
    def examiner_access(self, request, pk=None):
        resident = self.get_object()

        if request.method == "POST":
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            examiners = Examiner.objects.filter(user_id__in=serializer.validated_data["examiners"])
            current_examiners = Examiner.objects.filter(residents__resident=resident)

            ResidentAccess.objects.filter(resident=resident).exclude(
                examiner__in=examiners
            ).delete()
            ResidentAccess.objects.bulk_create(
                [
                    ResidentAccess(resident=resident, examiner=examiner)
                    for examiner in examiners
                    if examiner not in current_examiners
                ]
            )
            return response.Response({})
        else:
            return response.Response(
                [
                    {
                        "examiner": examiner_access.examiner.user.pk,
                        "primary": examiner_access.examiner.user.email
                        == resident.primary_doctor_email,
                    }
                    for examiner_access in ResidentAccess.objects.filter(resident=resident)
                ]
            )

    @action(methods=["POST"], detail=True)
    def request_examination(self, request, pk=None):
        resident = self.get_object()
        resident_examiners = Examiner.objects.filter(residents__resident=resident)
        requested_examiners = Examiner.objects.filter(
            examination_requests__resident=resident,
            examination_requests__status=ExaminationRequest.Status.sent,
        )
        ExaminationRequest.objects.bulk_create(
            [
                ExaminationRequest(resident=resident, examiner=examiner)
                for examiner in resident_examiners
                if examiner not in requested_examiners
            ]
        )
        return Response({}, status=status.HTTP_200_OK)


class CloudCareResidentsViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):

    queryset = Resident.objects.all()
    serializer_class = ResidentCloudCareSerializer
    permission_classes = [IsExternalClient]


class ResidentArchived1823sViewSet(ChildViewSetMixin, viewsets.ReadOnlyModelViewSet):
    parent_viewset = ResidentsViewSet
    queryset = Archived1823.objects.all()
    serializer_class = Archived1823Serializer
    permission_classes = [
        IsAuthenticated,
        IsRoleFor(FacilityUser.Role.account_admin, FacilityUser.Role.manager, methods=["GET"]),
    ]
    authentication_classes = [TimedAuthTokenAuthentication, ApiKeyUrlAuthentication]

    def get_queryset(self):
        return Archived1823.objects.filter(resident=self.parent_object)

    def retrieve(self, request, *args, **kwargs):
        archive = self.get_object()
        response = HttpResponse(archive.data_archived, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="Archived 1823 {} {}.pdf"'.format(
            archive.resident, archive.date_signed
        )
        return response


class ResidentsListPdfView(PdfView):
    queryset = Resident.objects.all()
    template_name = "residents/list.pdf.html"

    def get_title(self):
        title = "Resident List"
        title_param = self.request.query_params.get("title", "")
        if title_param:
            title = "{} - {}".format(title, title_param)
        return title

    def get_filename(self):
        return "{}.pdf".format(self.get_title())

    def get_residents(self):
        residents = self.get_queryset()
        resident_ids = self.get_resident_ids()
        residents = sorted(residents, key=lambda r: resident_ids.index(r.pk))
        return residents

    def get_queryset(self):
        queryset = super(ResidentsListPdfView, self).get_queryset()
        queryset = queryset.filter(facility=self.request.facility)
        queryset = queryset.filter(pk__in=self.get_resident_ids())
        return queryset

    def get_resident_ids(self):
        resident_ids_param = self.request.query_params.get("resident_ids", "")
        if not re.match(r"^\d[\d,]*$", resident_ids_param):
            return []
        return list(map(int, resident_ids_param.split(",")))

    def get_columns(self):
        columns_param = self.request.query_params.get("columns", "")
        if not columns_param:
            return None
        return columns_param.split(",")

    def get_context_data(self, **kwargs):
        context = super(ResidentsListPdfView, self).get_context_data(**kwargs)
        context["pdf_builder"] = ResidentListPdfBuilder(
            residents=self.get_residents(), columns=self.get_columns()
        )
        context["title"] = self.get_title()
        return context


class ResidentsAdmissionPdfView(PdfView):
    queryset = Resident.objects.all()
    template_name = "residents/admission.pdf.html"
    filename = "Admission List.pdf"

    def get_residents(self):
        residents = self.get_queryset()
        resident_ids = self.get_resident_ids()
        residents = sorted(residents, key=lambda r: resident_ids.index(r.pk))
        return residents

    def get_queryset(self):
        queryset = super(ResidentsAdmissionPdfView, self).get_queryset()
        queryset = queryset.filter(facility=self.request.facility)
        queryset = queryset.filter(pk__in=self.get_resident_ids())
        return queryset

    def get_resident_ids(self):
        resident_ids_param = self.request.query_params.get("resident_ids", "")
        if not re.match(r"^\d[\d,]*$", resident_ids_param):
            return []
        return list(map(int, resident_ids_param.split(",")))

    def get_context_data(self, **kwargs):
        context = super(ResidentsAdmissionPdfView, self).get_context_data(**kwargs)
        context["residents"] = self.get_residents()
        return context


class ResidentsFacesheetPdfView(PdfView):
    queryset = Resident.objects.all()
    template_name = "residents/facesheet.pdf.html"

    def get_queryset(self):
        queryset = super(ResidentsFacesheetPdfView, self).get_queryset()
        queryset = queryset.filter(facility=self.request.facility)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(ResidentsFacesheetPdfView, self).get_context_data(**kwargs)
        context["resident"] = self.get_object()
        return context

    def get_filename(self):
        return "{} Facesheet.pdf".format(self.get_object())


class Residents1823PdfView(PdfView):
    queryset = Resident.objects.all()
    template_name = "residents/1823.pdf.html"

    def get_queryset(self):
        queryset = super(Residents1823PdfView, self).get_queryset()
        queryset = queryset.filter(facility=self.request.facility)
        return queryset

    def get_context_data(self, **kwargs):
        self.resident = self.get_object()
        context = super(Residents1823PdfView, self).get_context_data(**kwargs)
        context["resident"] = self.resident
        context["resident_medication_numbers"] = list(range(1, 41))[
            self.resident.medications.count() :
        ]
        context["resident_services_offered_numbers"] = list(range(1, 16))[
            self.resident.services_offered.count() :
        ]
        context["resident_has_medication_files"] = self.resident.medication_files.exists()
        return context

    def get_filename(self):
        return "{} 1823.pdf".format(self.resident)

    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)
        resident = self.get_object()
        files = resident.medication_files.all().order_by("id")
        if files:
            response.content = merge_pdfs(response, files)
        return response


class ResidentsBlank1823PdfView(PdfView):
    queryset = Resident.objects.all()
    template_name = "residents/1823-blank.pdf.html"

    def get_queryset(self):
        queryset = super(ResidentsBlank1823PdfView, self).get_queryset()
        queryset = queryset.filter(facility=self.request.facility)
        return queryset

    def get_context_data(self, **kwargs):
        self.resident = self.get_object()
        context = super(ResidentsBlank1823PdfView, self).get_context_data(**kwargs)
        context["resident"] = self.resident
        return context

    def get_filename(self):
        return "{} 1823-blank.pdf"


class ResidentBedHoldViewSet(viewsets.ModelViewSet):
    queryset = ResidentBedHold.objects.all()
    serializer_class = ResidentBedHoldSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("resident",)
    permission_classes = [
        IsAuthenticated,
        FacilityHasResidentSubscription,
        IsSameFacilityForEditing,
        IsRoleFor(
            FacilityUser.Role.account_admin,
            FacilityUser.Role.manager,
            FacilityUser.Role.examiner,
            methods=["GET", "PATCH", "POST", "DELETE", "PUT"],
        ),
    ]

    def get_queryset(self):
        queryset = super(ResidentBedHoldViewSet, self).get_queryset()

        if self.request.role == FacilityUser.Role.examiner:
            queryset = queryset.filter(resident__examiners__examiner=self.request.user.examiner)

        return queryset.filter(resident__facility=self.request.facility)
