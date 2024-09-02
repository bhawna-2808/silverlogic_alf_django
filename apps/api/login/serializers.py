from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from actstream import action
from rest_framework import serializers

from apps.facilities.models import FacilityUser
from apps.subscriptions.models import Plan, Subscription

from ..facilities.serializers import TrainingsTimedAuthTokenCreateSerializer


class LoginSerializer(TrainingsTimedAuthTokenCreateSerializer):
    username = serializers.CharField()
    password = serializers.CharField()
    client_id = serializers.CharField()

    def validate_username(self, username):
        try:
            self.user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError(_("Username does not exist."))
        return username

    def validate_client_id(self, client_id):
        if (
            client_id != settings.WEB_CLIENT_ID
            and client_id != settings.APP_CLIENT_ID
            and client_id != settings.EXTERNAL_CLIENT_ID
        ):
            raise serializers.ValidationError(_("Please provide a valid client id"))
        return client_id

    def validate(self, data):

        if data["client_id"] == settings.EXTERNAL_CLIENT_ID:
            return data

        if not self.user.check_password(data["password"]):
            raise serializers.ValidationError({"password": _("Incorrect password.")})

        facility_user_qs = FacilityUser.objects.filter(user=self.user)
        if not facility_user_qs.exists():
            raise serializers.ValidationError(_("User is not associated to a facility."))

        employee = getattr(self.user, "employee", None)
        if employee and not employee.is_active:
            raise serializers.ValidationError(
                _(
                    "You are no longer associated with this Facility. Please contact your Facility Administrator"
                )
            )

        facility = facility_user_qs.first().facility
        if data["client_id"] == settings.APP_CLIENT_ID:
            subscription = (
                Subscription.objects.current()
                .filter(
                    facility=facility,
                    billing_interval__plan__module=Plan.Module.trainings,
                )
                .first()
            )
            if not subscription and not facility.sponsored_access:
                raise serializers.ValidationError(
                    _("Your facility doesn't have Trainings sponsorship, please contact support")
                )

        return data

    def create(self, validated_data):
        action.send(self.user, verb="logged in", action_object=self.user)
        return super(LoginSerializer, self).create(validated_data)
