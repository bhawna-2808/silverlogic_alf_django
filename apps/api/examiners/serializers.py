from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from apps.examiners.models import ExaminationRequest, ResidentAccess
from apps.residents.models import Resident


class ResidentAccessSerializer(serializers.Serializer):
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


class ExaminationRequestSerializer(serializers.ModelSerializer):
    examiner = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="examiner.user"
    )

    class Meta:
        model = ExaminationRequest
        fields = ("id", "resident", "examiner", "status")
        read_only_fields = ("status",)

    def validate_resident(self, resident):
        if resident.facility != self.context["request"].facility:
            raise serializers.ValidationError(
                _("You cannot request an examination of a resident that is not in your facility.")
            )
        return resident

    def validate_examiner(self, examiner):
        if examiner.facility_users.facility != self.context["request"].facility:
            raise serializers.ValidationError(
                _("You cannot request a non-facility-examiner to examine a resident.")
            )
        return examiner

    def validate(self, data):
        resident = data["resident"]
        examiner = data["examiner"]["user"]
        resident_accesses = ResidentAccess.objects.filter(
            resident=resident, examiner__user=examiner
        )
        if not resident_accesses.exists():
            raise serializers.ValidationError(
                _("The examiner does not have access to this resident.")
            )
        examination_request = ExaminationRequest.objects.filter(
            resident=resident,
            examiner__user=examiner,
            status=ExaminationRequest.Status.sent,
        )
        if examination_request.exists():
            raise serializers.ValidationError(
                _("The examiner has already been requested to examine this resident.")
            )
        return data

    def create(self, validated_data):
        validated_data["examiner"] = validated_data["examiner"]["user"].examiner
        return super(ExaminationRequestSerializer, self).create(validated_data)
