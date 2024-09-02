from django.contrib import admin

from .forms import FacilityUserForm
from .models import BusinessAgreement, FacilityUser, UserInvite, UserInviteResidentAccess


class FacilityUserAdmin(admin.ModelAdmin):
    search_fields = (
        "user__username",
        "user__email",
    )
    list_display = ("id", "user", "facility", "role", "user_employee")
    list_filter = ("role",)
    fields = (
        "user",
        "user_email",
        "user_employee",
        "facility",
        "role",
        "can_see_residents",
        "can_see_staff",
    )
    raw_id_fields = ("user",)
    readonly_fields = ("user_email", "user_employee")

    form = FacilityUserForm

    def user_email(self, instance):
        email = instance.user.email
        return email if email else "-"

    user_email.short_description = "User e-mail"

    def user_employee(self, instance):
        employee = instance.user.employee
        return employee if employee else "-"

    user_employee.short_description = "User employee"


class UserInviteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "facility",
        "email",
        "role",
        "invited_by",
        "status",
        "employee",
    )
    list_filter = (
        "role",
        "status",
    )
    fields = (
        "facility",
        "email",
        "role",
        "invited_by",
        "status",
        "employee",
        "can_see_residents",
        "can_see_staff",
    )
    readonly_fields = ("status",)


class UserInviteResidentAccessAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "invite",
        "resident",
    )


class BusinessAgreementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "facility",
        "get_user",
    )

    def get_user(self, obj):
        return "{} {}".format(obj.signed_by.user.first_name, obj.signed_by.user.last_name)

    get_user.short_description = "Signed By"
    get_user.admin_order_field = "signed_by__user__last_name"


admin.site.register(FacilityUser, FacilityUserAdmin)
admin.site.register(UserInvite, UserInviteAdmin)
admin.site.register(UserInviteResidentAccess, UserInviteResidentAccessAdmin)
admin.site.register(BusinessAgreement, BusinessAgreementAdmin)
