from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, serializers, viewsets

from apps.facilities.models import FacilityUser

from ..mixins import DestroyModelMixin
from ..permissions import IsRole
from .filters import UserFilter
from .serializers import UserSerializer, UserUpdateSerializer


class UsersViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsRole(FacilityUser.Role.account_admin)]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        queryset = super(UsersViewSet, self).get_queryset()
        queryset = queryset.filter(facility_users__facility=self.request.facility)
        return queryset

    def perform_destroy(self, instance):
        if instance.id == self.request.user.id:
            raise serializers.ValidationError(
                {"non_field_errors": _("You cannot delete yourself.")}
            )
        return super(UsersViewSet, self).perform_destroy(instance)
