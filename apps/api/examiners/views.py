from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, response, viewsets
from rest_framework.decorators import action

from apps.api.permissions import IsRole
from apps.examiners.models import ExaminationRequest, Examiner, ResidentAccess
from apps.facilities.models import FacilityUser
from apps.residents.models import Resident

from .serializers import ExaminationRequestSerializer, ResidentAccessSerializer


class ExaminersViewSet(viewsets.GenericViewSet):
    queryset = Examiner.objects.all()
    lookup_field = "user_id"
    permission_classes = [IsRole(FacilityUser.Role.account_admin)]

    def get_queryset(self):
        queryset = super(ExaminersViewSet, self).get_queryset()
        queryset = queryset.filter(user__facility_users__facility=self.request.facility)
        return queryset

    @action(methods=["GET", "POST"], serializer_class=ResidentAccessSerializer, detail=True)
    def resident_access(self, request, user_id=None):
        examiner = self.get_object()

        if request.method == "POST":
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            residents = serializer.validated_data["residents"]
            current_residents = Resident.objects.filter(examiners__examiner=examiner)

            ResidentAccess.objects.filter(examiner=examiner).exclude(
                resident__in=residents
            ).delete()
            ResidentAccess.objects.bulk_create(
                [
                    ResidentAccess(examiner=examiner, resident=resident)
                    for resident in residents
                    if resident not in current_residents
                ]
            )
            return response.Response({})
        else:
            return response.Response(
                {
                    "residents": [
                        resident_access.resident.pk
                        for resident_access in ResidentAccess.objects.filter(examiner=examiner)
                    ]
                }
            )


class ExaminationRequestsViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = ExaminationRequest.objects.all()
    permission_classes = [IsRole(FacilityUser.Role.account_admin)]
    serializer_class = ExaminationRequestSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ("resident", "status")
