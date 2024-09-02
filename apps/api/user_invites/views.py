from django.contrib.auth.models import User
from django.http import Http404
from django.utils.translation import gettext_lazy as _

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api.trainings.serializers import EmployeeReadSerializer
from apps.api.users.serializers import UserSerializer
from apps.facilities.models import UserInvite, UserInviteResidentAccess
from apps.trainings.models import Employee

from ..mixins import DestroyModelMixin
from .filters import UserInvitesFilter
from .permissions import IsAccountAdminOrManagerOrHasRetrieveToken
from .serializers import (
    UserInviteAcceptSerializer,
    UserInviteResidentAccessSerializer,
    UserInviteSerializer,
)


class UserInvitesViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = UserInvite.objects.all()
    serializer_class = UserInviteSerializer
    permission_classes = [IsAccountAdminOrManagerOrHasRetrieveToken]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserInvitesFilter

    def get_queryset(self):
        queryset = super(UserInvitesViewSet, self).get_queryset()
        if self.request.user.is_authenticated:
            queryset = queryset.filter(facility=self.request.facility)
        return queryset

    @action(
        methods=["GET", "POST"],
        serializer_class=UserInviteResidentAccessSerializer,
        detail=True,
    )
    def resident_access(self, request, pk=None):
        invite = self.get_object()

        if request.method == "POST":
            if invite.status == UserInvite.Status.accepted:
                raise serializers.ValidationError(
                    _(
                        "This invitation has already been accepted. You can change residents access in Facility Examiners details."
                    )
                )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            residents = serializer.validated_data["residents"]

            UserInviteResidentAccess.objects.filter(invite=invite).delete()
            UserInviteResidentAccess.objects.bulk_create(
                [
                    UserInviteResidentAccess(invite=invite, resident=resident)
                    for resident in residents
                ]
            )
            return Response({})
        else:
            return Response(
                {
                    "residents": [
                        resident_access.resident.pk
                        for resident_access in UserInviteResidentAccess.objects.filter(
                            invite=invite
                        )
                    ]
                }
            )

    @action(methods=["POST"], detail=False)
    def employee_link(self, request, pk=None):
        if request.data.get("employee", None):
            employee = Employee.objects.get(pk=request.data.get("employee"))
            if employee.user:
                if not hasattr(employee.user, "facility_user"):
                    raise serializers.ValidationError(
                        _("User not linked to a Facility. Please contact with support.")
                    )
                raise serializers.ValidationError(_("The selected Employee has an user linked."))

            if request.data.get("user", None):
                user = User.objects.get(pk=request.data.get("user"))
                employee.user = user
                employee.save()
                return Response(
                    {
                        "user": UserSerializer(user).data,
                        "employee": EmployeeReadSerializer(employee).data,
                    }
                )
        return Response({})

    @action(
        methods=["POST"],
        serializer_class=UserInviteAcceptSerializer,
        permission_classes=[],
        detail=True,
    )
    def accept(self, request, pk=None):
        try:
            invite = self.get_object()
        except Http404:
            return Response(
                {"token": [_("Your invite is invalid.  You will not be able to create a user.")]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(instance=invite, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({})
