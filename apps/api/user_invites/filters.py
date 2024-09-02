import django_filters

from apps.facilities.models import UserInvite


class UserInvitesFilter(django_filters.FilterSet):
    resident = django_filters.NumberFilter(method="filter_resident")

    class Meta:
        model = UserInvite
        fields = ("role", "status", "resident")

    def filter_resident(self, queryset, name, value):
        queryset = queryset.filter(resident_accesses__resident=value)
        return queryset
