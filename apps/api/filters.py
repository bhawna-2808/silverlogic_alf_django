from datetime import date

from django.db.models import CharField, F, Value
from django.db.models.functions import Concat

import django_filters
from django_filters.rest_framework.filters import BooleanFilter, CharFilter

from apps.base.helpers import parse_string_to_timedelta
from apps.trainings.models import (
    CustomTaskType,
    Employee,
    Task,
    TaskHistory,
    TaskType,
    TrainingEvent,
)


class TaskFilter(django_filters.FilterSet):
    is_training = django_filters.BooleanFilter(field_name="type__is_training")
    due_date_limit = CharFilter(method="filter_due_date_limit")

    class Meta:
        model = Task
        fields = "employee", "type", "status", "is_training", "type__course__language"

    def filter_due_date_limit(self, qs, name, value):
        timedelta = parse_string_to_timedelta(value)
        limit = date.today() + timedelta
        return qs.filter(due_date__lte=limit)


class TaskHistoryFilter(django_filters.FilterSet):
    is_training = django_filters.BooleanFilter(field_name="type__is_training")

    class Meta:
        model = TaskHistory
        fields = (
            "employee",
            "type",
            "status",
            "is_training",
        )


class TaskTypeFilter(django_filters.FilterSet):
    is_training = django_filters.BooleanFilter(field_name="is_training")

    class Meta:
        model = TaskType
        fields = "name", "is_training"


class CustomTaskTypeFilter(django_filters.FilterSet):
    is_training = django_filters.BooleanFilter(field_name="is_training")

    class Meta:
        model = CustomTaskType
        fields = "name", "is_training"


class TrainingEventFilter(django_filters.FilterSet):
    class Meta:
        model = TrainingEvent
        fields = "training_for", "completed"


class EmployeeFilter(django_filters.FilterSet):
    full_name = CharFilter(method="filter_full_name")
    not_linked = BooleanFilter(method="filter_not_linked", label="Not linked Employee Users")

    class Meta:
        model = Employee
        fields = "full_name", "is_active", "not_linked"

    def filter_full_name(self, qs, name, value):
        return qs.annotate(
            filter_full_name=Concat(
                F("first_name"), Value(" "), F("last_name"), output_field=CharField()
            )
        ).filter(filter_full_name__icontains=value)

    def filter_not_linked(self, queryset, name, value):
        return queryset.filter(user__isnull=value)
