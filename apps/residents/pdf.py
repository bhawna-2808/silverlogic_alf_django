from datetime import date

from django.utils.safestring import mark_safe

from .models import Resident


class ResidentListPdfBuilder:
    DEFAULT_COLUMNS = [
        "first_name",
        "last_name",
        "examination_due_date",
        "room_number",
        "bed",
    ]

    def __init__(self, residents, columns=None):
        self.residents = residents
        self.column_names = columns or self.DEFAULT_COLUMNS

    def columns(self):
        return [ResidentListPdfColumn(field_name) for field_name in self.column_names]

    def rows(self):
        return [ResidentListPdfRow(builder=self, resident=resident) for resident in self.residents]


class ResidentListPdfRow:
    def __init__(self, builder, resident):
        self.builder = builder
        self.resident = resident

    def columns(self):
        return [
            ResidentListPdfColumn(field_name, resident=self.resident)
            for field_name in self.builder.column_names
        ]


class ResidentListPdfColumn:
    EXTRA_FIELDS = ["case_worker", "diet"]

    def __init__(self, field_name, resident=None):
        self.field_name = field_name
        self.resident = resident

    @property
    def name(self):
        field = getattr(self, self.field_name, None)
        if not field:
            field = Resident._meta.get_field(self.field_name)
        return field.verbose_name

    @property
    def value(self):
        field = getattr(self, self.field_name, None)
        if field:
            value = field()
        else:
            value = getattr(self.resident, self.field_name)
        if isinstance(value, date):
            value = value.strftime("%m/%d/%Y")
        return value

    def has_assistive_care_services(self):
        return "ACS" if self.resident.has_assistive_care_services else ""

    has_assistive_care_services.verbose_name = "Status"

    def examination_due_date(self):
        return self.resident.examination_due_date

    examination_due_date.verbose_name = "1823 Exam Due"

    def case_worker(self):
        return "{}, {}".format(
            self.resident.case_worker_last_name, self.resident.case_worker_first_name
        )

    case_worker.verbose_name = "Case Worker"

    def diet(self):
        diets = []
        if self.resident.is_diet_regular:
            diets.append("regular")
        if self.resident.is_diet_calorie_controlled:
            diets.append("calorie controlled")
        if self.resident.is_diet_no_added_salt:
            diets.append("no added salt")
        if self.resident.is_diet_low_fat_or_low_cholesterol:
            diets.append("low fat or low cholesterol")
        if self.resident.is_diet_low_sugar:
            diets.append("low sugar")
        if self.resident.is_diet_other:
            diets.append("other")
        s = ";<br /> ".join(diets)
        if self.resident.diet_other_comments:
            s += ": %s" % self.resident.diet_other_comments
        return mark_safe(s)

    diet.verbose_name = "Diet"
