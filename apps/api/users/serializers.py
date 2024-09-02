from django.contrib.auth.models import User

from rest_framework import serializers

from apps.api.facilities.serializers import FacilityUserSerializer, UserResidentAccessSerializer
from apps.facilities.models import FacilityUser, UserResidentAccess

from ..serializers import ModelSerializer


class UserUpdateSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("id",)

    def to_internal_value(self, data):
        if "resident_access" in data:
            self.resident_access = data["resident_access"]
        if "facility_user" in data:
            self.facility_user = data["facility_user"]
        return data

    def update(self, instance, validated_data):
        return_value = super(UserUpdateSerializer, self).update(instance, validated_data)

        if hasattr(self, "resident_access"):
            # Create a new UserResidentAccess if does not exist
            # It is not necessary to exist, because by default, manager
            # is allowed to see all the residents
            for resident_access in self.resident_access:
                is_allowed = resident_access["is_allowed"]
                resident_id = resident_access["resident"]

                UserResidentAccess.objects.update_or_create(
                    user=instance.facility_users,
                    resident_id=resident_id,
                    defaults={
                        "is_allowed": is_allowed,
                    },
                )

        if hasattr(self, "facility_user"):
            facility_user = instance.facility_users
            facility_user.can_see_residents = validated_data["facility_user"]["can_see_residents"]
            facility_user.can_see_staff = validated_data["facility_user"]["can_see_staff"]
            facility_user.save()

        return return_value


class UserSerializer(ModelSerializer):
    role = serializers.SerializerMethodField()
    resident_access = serializers.SerializerMethodField()
    facility_user = FacilityUserSerializer(source="facility_users")

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "is_superuser",
            "first_name",
            "last_name",
            "email",
            "role",
            "resident_access",
            "facility_user",
        )

    def get_role(self, user):
        facility_user = FacilityUser.objects.get(user=user)
        return facility_user.role

    def get_resident_access(self, user):
        facility_user = FacilityUser.objects.get(user=user)
        if facility_user.role != FacilityUser.Role.manager:
            return []

        resident_accesses = UserResidentAccess.objects.filter(user=facility_user)
        return [
            UserResidentAccessSerializer(resident_access).data
            for resident_access in resident_accesses
        ]

    def get_facility_user(self, user):
        facility_user = FacilityUser.objects.get(user=user)
        if facility_user.role != FacilityUser.Role.manager:
            return []

        resident_accesses = UserResidentAccess.objects.filter(user=facility_user)
        return [
            UserResidentAccessSerializer(resident_access).data
            for resident_access in resident_accesses
        ]
