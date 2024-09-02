import re

from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from apps.alfdirectory.models import Facility as DirectoryFacility
from apps.facilities.models import FacilityUser
from apps.trainings.models import Employee, Facility

from ..facilities.serializers import FacilitySerializer
from ..serializers import ModelSerializer


class DirectoryFacilitySerializer(ModelSerializer):
    class Meta:
        model = DirectoryFacility
        fields = (
            "id",
            "license_number",
            "name",
        )


class RegisterFacilitySerializer(ModelSerializer):
    license_number = serializers.CharField(max_length=100, required=False)

    class Meta:
        model = Facility
        fields = (
            "id",
            "name",
            "license_number",
            "directory_facility",
            "questions",
            "address_line1",
            "address_line2",
            "address_city",
            "address_county",
            "tax_id",
            "state",
            "address_zipcode",
            "contact_phone",
            "contact_email",
            "npi",
            "fcc_signup",
        )
        extra_kwargs = {"state": {"required": True, "allow_null": False}}

    def _validate_license_number(self, license_number, data):
        if license_number:
            facilities = list(DirectoryFacility.objects.filter(license_number=license_number))
            if not facilities:
                raise serializers.ValidationError(
                    {"license_number": _("Please enter a valid Florida ALF license number.")}
                )
            if len(facilities) > 1:
                raise serializers.ValidationError(
                    {
                        "directory_facility": {
                            "message": [
                                "{} facilities with license number {}, please select yours".format(
                                    len(facilities), license_number
                                )
                            ],
                            "facilities": DirectoryFacilitySerializer(facilities, many=True).data,
                        }
                    }
                )
            data["directory_facility"] = facilities[0]
            del data["license_number"]

    def validate(self, data):
        directory_facility = data.get("directory_facility", None)
        license_number = data.get("license_number", None)

        if directory_facility and license_number or (not directory_facility and not license_number):
            raise serializers.ValidationError(
                {"license_number": _("Either license_number or directory_facility is required.")}
            )

        self._validate_license_number(license_number, data)

        return data


class RegisterUserSerializer(ModelSerializer):
    conf_password = serializers.CharField()

    class Meta:
        model = User
        fields = (
            "username",
            "password",
            "conf_password",
            "first_name",
            "last_name",
            "email",
        )
        extra_kwargs = {
            "first_name": {"required": True, "allow_blank": False},
            "last_name": {"required": True, "allow_blank": False},
            "email": {"required": True, "allow_blank": False},
        }

    def validate(self, data):
        password = data["password"]
        conf_password = data.pop("conf_password")

        if password != conf_password:
            raise serializers.ValidationError("Passwords do not match")
        return data


class RegisterTermsSerializer(serializers.Serializer):
    agree = serializers.BooleanField()

    def validate_agree(self, agree):
        if not agree:
            raise serializers.ValidationError(
                "You must agree to the terms and conditions " "before you can proceed"
            )
        return agree


class RegisterSerializer(serializers.Serializer):
    facility = RegisterFacilitySerializer()
    user = RegisterUserSerializer()
    terms = RegisterTermsSerializer()

    def create(self, validated_data):
        if "fcc_signup" in validated_data["facility"] and validated_data["facility"]["fcc_signup"]:
            validated_data["facility"]["is_staff_module_enabled"] = False
        facility_questions_data = validated_data["facility"].pop("questions", [])
        validated_data["facility"]["primary_administrator_name"] = "{} {}".format(
            validated_data["user"]["first_name"], validated_data["user"]["last_name"]
        )
        validated_data["facility"]["capacity"] = validated_data["facility"][
            "directory_facility"
        ].capacity
        facility = Facility.objects.create(**validated_data["facility"])
        facility.questions.add(*facility_questions_data)

        user_data = validated_data.pop("user")
        user = User.objects.create_user(**user_data)
        user.unsafe_password = user_data["password"]  # Used for welcome email.

        FacilityUser.objects.create(
            facility=facility, user=user, role=FacilityUser.Role.account_admin
        )

        return {
            "facility": facility,
            "user": user,
        }

    def to_representation(self, obj):
        return {
            "facility": FacilitySerializer(obj["facility"]).data,
        }


class EmployeeRegisterSerializer(ModelSerializer):
    phone = serializers.CharField()
    conf_password = serializers.CharField()

    class Meta:
        model = User
        fields = (
            "username",
            "password",
            "conf_password",
            "phone",
        )

    def validate(self, data):
        password = data["password"]
        conf_password = data.pop("conf_password")

        if password != conf_password:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def validate_phone(self, phone):
        phone_list = re.findall(r"\d", phone)
        if len(phone_list) != 10:
            raise serializers.ValidationError("The phone number must have 10 digits")
        return "({}{}{}) {}{}{}-{}{}{}{}".format(*phone_list)

    def create(self, validated_data):
        _phone = validated_data.pop("phone")
        user_data = validated_data
        employee = Employee.objects.filter(phone_number=_phone).first()
        if not employee:
            raise serializers.ValidationError(
                {"phone": ["No employee record found for your phone number"]}
            )
        user_data["first_name"] = employee.first_name
        user_data["last_name"] = employee.last_name
        user_data["email"] = employee.email
        user = User.objects.create_user(**user_data)
        employee.user = user
        if not employee.email:
            employee.email = user.email
        employee.save()

        FacilityUser.objects.create(
            facility=employee.facility, user=user, role=FacilityUser.Role.trainings_user
        )

        return {
            "employee": employee,
            "user": user,
        }
