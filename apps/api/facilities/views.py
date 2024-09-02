from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt

from rest_framework import mixins, viewsets
from rest_framework.decorators import action

from apps.api.authentication import ApiKeyUrlAuthentication
from apps.facilities.models import BusinessAgreement, FacilityUser
from apps.facilities.utils import generate_pdf
from apps.trainings.models import Facility, FacilityQuestion

from ..permissions import IsAuthenticated, IsExternalClient, IsRole, IsRoleForUpdate, IsSameFacility
from .serializers import (
    BusinessAgreementSerializer,
    FacilityCloudCareSerializer,
    FacilityQuestionSerializer,
    FacilitySerializer,
)


class FacilityViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Facility.objects.all().prefetch_related(
        "questions",
        "questions__rules",
        "businessagreement",
    )
    serializer_class = FacilitySerializer
    permission_classes = [
        IsAuthenticated,
        IsRoleForUpdate(FacilityUser.Role.account_admin),
    ]

    def get_queryset(self):
        queryset = super(FacilityViewSet, self).get_queryset()
        queryset = queryset.filter(pk=self.request.facility.pk)
        return queryset


class FacilityQuestionViewSet(viewsets.ModelViewSet):
    queryset = FacilityQuestion.objects.all()
    serializer_class = FacilityQuestionSerializer


class BusinessAgreementViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = BusinessAgreement.objects.all()
    serializer_class = BusinessAgreementSerializer
    permission_classes = (
        IsSameFacility,
        IsRole(FacilityUser.Role.account_admin),
    )

    def perform_create(self, serializer):
        serializer.save(signed_by=self.request.user.facility_users, facility=self.request.facility)

    @xframe_options_exempt
    @action(methods=["GET"], authentication_classes=(ApiKeyUrlAuthentication,), detail=False)
    def new(self, request):
        response = HttpResponse(content_type="application/pdf")
        generate_pdf(response, request.facility, request.user)
        response["Content-Disposition"] = 'filename="Business Agreement - {}.pdf"'.format(
            request.facility.name
        )
        return response

    @action(methods=["GET"], authentication_classes=(ApiKeyUrlAuthentication,), detail=True)
    def download(self, request, pk=None):
        business_agreement = self.get_object()
        response = HttpResponse(business_agreement.pdf.read(), content_type="application/pdf")
        response["Content-Disposition"] = "filename=Business Agreement - {}.pdf".format(
            business_agreement.facility.name
        )
        return response


class CloudCareFacilityViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    queryset = Facility.objects.all()
    permission_classes = [IsExternalClient]
    serializer_class = FacilityCloudCareSerializer
