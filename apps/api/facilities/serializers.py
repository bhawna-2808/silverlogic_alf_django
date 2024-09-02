import logging
from tempfile import TemporaryFile

from django.core.files import File
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from constance import config
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from timed_auth_token.serializers import (
    TimedAuthTokenCreateSerializer,
    TimedAuthTokenReadSerializer,
)

from apps.api.fields import ThumbnailImageField
from apps.facilities.models import (
    BusinessAgreement,
    FacilityUser,
    TrainingsTimedAuthToken,
    UserResidentAccess,
)
from apps.facilities.utils import generate_pdf
from apps.subscriptions.models import BillingInterval, Plan, Subscription
from apps.trainings.models import (
    Employee,
    Facility,
    FacilityDefault,
    FacilityQuestion,
    FacilityQuestionRule,
)

from ..serializers import ModelSerializer

logger = logging.getLogger(__name__)


class UserResidentAccessSerializer(ModelSerializer):
    class Meta:
        model = UserResidentAccess
        fields = ("id", "user", "resident", "is_allowed")


class FacilityQuestionRuleSerializer(ModelSerializer):
    class Meta:
        model = FacilityQuestionRule
        fields = "__all__"


class FacilityQuestionSerializer(ModelSerializer):
    rules = FacilityQuestionRuleSerializer(many=True, read_only=True)

    class Meta:
        model = FacilityQuestion
        fields = "__all__"


class FacilityDefaultSerializer(ModelSerializer):
    class Meta:
        model = FacilityDefault
        fields = "__all__"


class FacilitySerializer(ModelSerializer):
    admin_signature = ThumbnailImageField(write_only=True, required=False)

    class Meta:
        model = Facility
        fields = "__all__"
        read_only_fields = ("capacity",)

    def to_internal_value(self, data):
        if "license_number" in data:
            self.license_number = data["license_number"]
        return super(FacilitySerializer, self).to_internal_value(data)

    def to_representation(self, obj):
        return FacilityReadSerializer(instance=obj).data

    def create_automatic_subscription(self, facility, start_date):
        billing_interval = BillingInterval.objects.filter(
            interval="month", plan__module="trainings", plan__capacity_limit=14
        ).first()
        if not billing_interval:
            logger.exception("Couldn't get billing interval for automatic trainings subscription")
            return False
        if facility.subscriptions.filter(status="active").count() > 0:
            if not Subscription.objects.filter(
                facility=facility,
                billing_interval=billing_interval,
                status="active",
                current_period_start=start_date,
            ).exists():
                Subscription.objects.create(
                    facility=facility,
                    billing_interval=billing_interval,
                    status="active",
                    current_period_start=start_date,
                )
            return True
        return False

    def update(self, instance, validated_data):
        facility = super(FacilitySerializer, self).update(instance, validated_data)
        if hasattr(self, "license_number"):
            df = facility.directory_facility
            df.license_number = self.license_number
            df.save()

        if "opted_in_sponsorship_date" in validated_data:
            request = self.context["request"]
            subscription_created = self.create_automatic_subscription(
                facility, validated_data["opted_in_sponsorship_date"]
            )
            context = {
                "facility": facility,
                "user": request.user,
                "url": request.build_absolute_uri(
                    reverse("admin:subscriptions_optedinfacility_changelist")
                ),
                "url_subscriptions": request.build_absolute_uri(
                    reverse("admin:subscriptions_subscription_add")
                ),
                "subscription_created": subscription_created,
            }
            alf_emails = config.ALF_ADMIN_EMAILS.replace(" ", "").split(",")
            subject = render_to_string("facilities/emails/opt-in-subject.txt", context).strip()
            message = render_to_string("facilities/emails/opt-in-body.txt", context)
            html_message = render_to_string("facilities/emails/opt-in-body.html", context)
            email = EmailMultiAlternatives(subject, message, from_email=None, to=alf_emails)
            email.attach_alternative(html_message, "text/html")
            email.send()
        return facility


class FacilityCloudCareSerializer(ModelSerializer):
    class Meta:
        model = Facility
        fields = ("id", "name")


class EmployeeSimpleSerializer(ModelSerializer):
    class Meta:
        model = Employee
        fields = ("id", "phone_number", "email", "full_name")

    def get_full_name(self, employee):
        return "{} {}".format(employee.first_name, employee.last_name)


class FacilityUserSerializer(ModelSerializer):
    employee = serializers.SerializerMethodField()

    class Meta:
        model = FacilityUser
        fields = ("can_see_residents", "can_see_staff", "employee")

    def get_employee(self, facility_user):

        if hasattr(facility_user.user, "employee"):
            return EmployeeSimpleSerializer(facility_user.user.employee).data
        return None


class BusinessAgreementSerializer(ModelSerializer):
    signature = ThumbnailImageField(write_only=True)

    class Meta:
        model = BusinessAgreement
        fields = (
            "id",
            "signature",
        )

    def validate(self, attrs):
        if BusinessAgreement.objects.filter(facility=self.context["request"].facility).exists():
            raise ValidationError("Your facility has already signed a business agreement.")
        return attrs

    def create(self, validated_data):
        validated_data["pdf"] = File(name="Business Agreement.pdf", file=TemporaryFile())
        generate_pdf(
            validated_data["pdf"],
            self.context["request"].facility,
            self.context["request"].user,
            validated_data.pop("signature", None),
        ),
        return super(BusinessAgreementSerializer, self).create(validated_data)


class FacilityReadSerializer(ModelSerializer):
    questions = FacilityQuestionSerializer(many=True)
    first_aid_cpr = serializers.SerializerMethodField()
    alzheimer = serializers.SerializerMethodField()
    default = FacilityDefaultSerializer()
    can_use_subscription_trial = serializers.SerializerMethodField()
    has_active_subscription = serializers.SerializerMethodField()
    has_active_trainings_subscription = serializers.SerializerMethodField()
    has_active_non_trail_subscription = serializers.SerializerMethodField()
    businessagreement = BusinessAgreementSerializer()
    license_number = serializers.CharField(
        source="directory_facility.license_number", read_only=True
    )

    class Meta:
        model = Facility
        fields = "__all__"

    def get_first_aid_cpr(self, facility):
        return facility.first_aid_cpr

    def get_alzheimer(self, facility):
        return facility.alzheimer

    def get_can_use_subscription_trial(self, facility):
        return not Subscription.objects.filter(facility=facility).exists()

    def get_has_active_subscription(self, facility):
        return (
            facility.fcc_signup
            or Subscription.objects.filter(facility=facility).is_active().exists()
        )

    def get_has_active_non_trail_subscription(self, facility):
        return (
            facility.fcc_signup
            or Subscription.objects.filter(status="active", facility=facility).exists()
        )

    def get_has_active_trainings_subscription(self, facility):
        return (
            facility.fcc_signup
            or Subscription.objects.filter(
                facility=facility, billing_interval__plan__module=Plan.Module.trainings
            )
            .is_active()
            .exists()
        )


class TrainingsTimedAuthTokenCreateSerializer(TimedAuthTokenCreateSerializer):
    def create(self, validated_data):
        return TrainingsTimedAuthToken.objects.create(user=self.user)

    def to_representation(self, token):
        return TrainingsTimedAuthTokenReadSerializer(token).data


class TrainingsTimedAuthTokenReadSerializer(TimedAuthTokenReadSerializer):
    class Meta:
        model = TrainingsTimedAuthToken
