from django.db.models import F, Value
from django.db.models.functions import Concat

import django_filters
from django_filters.rest_framework.filters import CharFilter

from apps.residents.models import Resident


class ResidentFilter(django_filters.FilterSet):
    full_name = CharFilter(method="filter_full_name")

    class Meta:
        model = Resident
        fields = (
            "full_name",
            "is_active",
        )

    def filter_full_name(self, qs, name, value):
        return qs.annotate(
            filter_full_name=Concat(F("first_name"), Value(" "), F("last_name"))
        ).filter(filter_full_name__icontains=value)
