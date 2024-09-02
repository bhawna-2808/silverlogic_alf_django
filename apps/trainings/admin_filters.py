from django.contrib import admin

from .models import Employee, Facility


class EmployeeListFilter(admin.SimpleListFilter):
    title = "employee"
    parameter_name = "employee"

    def lookups(self, request, model_admin):
        qs = Employee.objects.all().order_by("first_name", "last_name")
        return [(e.pk, str(e)) for e in qs]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(employee__pk=self.value())


class EmployeeFacilityListFilter(admin.SimpleListFilter):
    title = "facility"
    parameter_name = "facility"

    def lookups(self, request, model_admin):
        qs = Facility.objects.all().order_by("name")
        return [(e.pk, str(e)) for e in qs]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(employee__facility__pk=self.value())


class CapacityFacilityListFilter(admin.SimpleListFilter):
    title = "capacity"
    parameter_name = "capacity"

    def lookups(self, request, model_admin):
        return (
            ("is_set", ("Is set")),
            ("not_set", ("Not set")),
        )

    def queryset(self, request, queryset):
        if self.value() == "is_set":
            return queryset.exclude(capacity=0)
        if self.value() == "not_set":
            return queryset.filter(capacity=0)
