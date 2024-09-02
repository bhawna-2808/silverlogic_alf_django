from django.contrib.auth.models import User

import django_filters
from django_filters.rest_framework.filters import BooleanFilter

from apps.facilities.models import FacilityUser


class UserFilter(django_filters.FilterSet):
    role = django_filters.ChoiceFilter(choices=FacilityUser.Role, method="filter_role")
    not_linked = BooleanFilter(method="filter_not_linked", label="Not Linked Employee Users")

    class Meta:
        model = User
        fields = ("role", "not_linked")

    def filter_role(self, queryset, name, value):
        return queryset.filter(facility_users__role=value)

    def filter_not_linked(self, queryset, name, value):
        return queryset.filter(employee__isnull=value)
