from django.contrib import admin

from .models import ExaminationRequest, Examiner, ResidentAccess


class ExaminerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "medical_license_number",
    )


class ResidentAccessAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "examiner",
        "resident",
    )


class ExaminationRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "examiner", "resident", "status")


admin.site.register(Examiner, ExaminerAdmin)
admin.site.register(ResidentAccess, ResidentAccessAdmin)
admin.site.register(ExaminationRequest, ExaminationRequestAdmin)
