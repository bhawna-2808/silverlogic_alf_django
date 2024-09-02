import django_filters
from django_filters.rest_framework import CharFilter

from apps.trainings.models import Course


class CourseFilter(django_filters.FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Course
        fields = ("published", "language", "name")
