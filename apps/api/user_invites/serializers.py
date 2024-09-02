from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from django_fsm import can_proceed
from rest_framework import serializers

from apps.api.trainings.serializers import EmployeeSimpleSerializer
from apps.facilities.models import FacilityUser, UserInvite
from apps.facilities.tokens import UserInviteTokenGenerator
from apps.residents.models import Resident

from ..serializers import AutoFacilityMixin, ModelSerializer


class UserInviteSerializer(AutoFacilityMixin, ModelSerializer):

    employee_detail = EmployeeSimpleSerializer(source="employee", read_only=True)

    class Meta:
        model = UserInvite
        fields = (
            "id",
            "email",
            "phone_number",
            "role",
            "status",
            "employee",
            "employee_detail",
            "can_see_residents",
            "can_see_staff",
        )
        read_only_fields = ("status",)

    def validate_email(self, email):
        facility_users = FacilityUser.objects.filter(
            user__email=email, facility=self.context["request"].facility
        )
        if facility_users.exists():
            raise serializers.ValidationError(
                {
                    "message": _("A user with that email is already present in your facility."),
                    "user_id": facility_users.first().user.pk,
                }
            )
        return email

    def create(self, validated_data):
        try:
            user_invite = UserInvite.objects.get(
                email=validated_data["email"], facility=self.context["request"].facility
            )
        except UserInvite.DoesNotExist:
            validated_data["invited_by"] = self.context["request"].user
            user_invite = super(UserInviteSerializer, self).create(validated_data)
            self.fill_employee_info(user_invite)
            return user_invite
        else:
            if "can_see_residents" in validated_data:
                user_invite.can_see_residents = validated_data["can_see_residents"]
            if "can_see_staff" in validated_data:
                user_invite.can_see_staff = validated_data["can_see_staff"]
            user_invite.save()
            user_invite.send()
            return user_invite

    def fill_employee_info(self, user_invite):
        if getattr(user_invite, "employee", None):
            employee = user_invite.employee
            if not getattr(employee, "email", None):
                employee.email = user_invite.email
                employee.save()

            if getattr(user_invite, "phone_number", None):
                if not getattr(employee, "phone_number", None):
                    employee.phone_number = user_invite.phone_number
                    employee.save()


class UserInviteResidentAccessSerializer(serializers.Serializer):
    residents = serializers.PrimaryKeyRelatedField(queryset=Resident.objects.all(), many=True)

    def validate_residents(self, residents):
        for resident in residents:
            if resident.facility != self.context["request"].facility:
                raise serializers.ValidationError(
                    _(
                        "You cannot grant an examiner access to residents that are not in your facility."
                    )
                )
        return residents


class UserInviteAcceptSerializer(ModelSerializer):
    token = serializers.CharField()
    medical_license_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "token",
            "username",
            "password",
            "first_name",
            "last_name",
            "medical_license_number",
        )
        extra_kwargs = {
            "first_name": {"required": True, "allow_blank": False},
            "last_name": {"required": True, "allow_blank": False},
        }

    def validate_token(self, token):
        if not UserInviteTokenGenerator().check_token(invite=self.instance, token=token):
            raise serializers.ValidationError(
                _("Your invite is invalid.  You will not be able to create a user.")
            )
        return token

    def validate(self, data):
        if not can_proceed(self.instance.accept):
            raise serializers.ValidationError(
                _("This invitation has already been accepted.  You may now login.")
            )
        if self.instance.role == UserInvite.Role.examiner and not data.get(
            "medical_license_number"
        ):
            raise serializers.ValidationError(
                {"medical_license_number": [_("This field is required.")]}
            )
        return data

    def update(self, instance, validated_data):
        validated_data.pop("token")
        user = instance.accept(**validated_data)
        instance.save()
        return user
