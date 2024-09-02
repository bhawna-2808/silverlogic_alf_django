import logging
from datetime import datetime

from django.utils.translation import gettext_lazy as _

import pytz
import stripe
from expander import ExpanderSerializerMixin
from rest_framework import serializers

from apps.subscriptions.models import FacilityPaymentMethod, Plan, Sponsor, Subscription

from ..plans.serializers import BillingIntervalSerializer
from ..serializers import ModelSerializer

logger = logging.getLogger(__name__)


def _timestamp_to_utc_datetime(timestamp):
    return datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.UTC)


class SubscriptionSerializer(ExpanderSerializerMixin, ModelSerializer):
    stripe_token = serializers.CharField(write_only=True)
    has_stripe_id = serializers.BooleanField(source="stripe_id", read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "stripe_token",
            "id",
            "billing_interval",
            "status",
            "current_period_start",
            "current_period_end",
            "trial_start",
            "trial_end",
            "has_stripe_id",
        )
        read_only_fields = ("status", "current_period_start", "current_period_end")
        expandable_fields = {
            "billing_interval": BillingIntervalSerializer,
        }

    def validate(self, data):
        facility = self.context["request"].facility
        if (
            not self.instance
            and facility.subscriptions.current()
            .filter(billing_interval__plan__module=data["billing_interval"].plan.module)
            .exclude(status=Subscription.Status.trialing)
            .exists()
        ):
            raise serializers.ValidationError(
                _("You already have a {} module subscription.").format(
                    data["billing_interval"].plan.module
                )
            )
        if not hasattr(facility, "businessagreement"):
            if not self.instance and data["billing_interval"].plan.module == Plan.Module.resident:
                raise serializers.ValidationError(
                    _(
                        "You need to sign a business agreement before starting a resident module subscription."
                    )
                )
            if self.instance and self.instance.billing_interval.plan.module == Plan.Module.resident:
                raise serializers.ValidationError(
                    _(
                        "You need to sign a business agreement before updating a resident module subscription."
                    )
                )
        return data

    def create(self, validated_data):
        validated_data["facility"] = self.context["request"].facility

        stripe_customer = self.create_stripe_customer(
            validated_data.pop("stripe_token"),
            validated_data["billing_interval"],
            validated_data["facility"],
        )
        stripe_subscription = stripe_customer.subscriptions.data[0]
        validated_data["stripe_id"] = stripe_subscription.id
        validated_data["current_period_start"] = _timestamp_to_utc_datetime(
            stripe_subscription.current_period_start
        )
        validated_data["current_period_end"] = _timestamp_to_utc_datetime(
            stripe_subscription.current_period_end
        )
        validated_data["trial_start"] = (
            _timestamp_to_utc_datetime(stripe_subscription.trial_start)
            if stripe_subscription.trial_start
            else None
        )
        validated_data["trial_end"] = (
            _timestamp_to_utc_datetime(stripe_subscription.trial_end)
            if stripe_subscription.trial_end
            else None
        )

        return super(SubscriptionSerializer, self).create(validated_data)

    def create_stripe_customer(self, stripe_token, billing_interval, facility):
        trial = (
            facility.subscriptions.current()
            .filter(
                billing_interval__plan__module=billing_interval.plan.module,
                status=Subscription.Status.trialing,
            )
            .first()
        )
        trial_end = trial.trial_end if trial and trial.trial_end else None
        try:
            stripe_customer = stripe.Customer.create(
                source=stripe_token,
                plan=billing_interval.stripe_id,
                description=facility.name,
                trial_end=trial_end,
            )
            if trial and trial.trial_end:
                trial.status = Subscription.Status.canceled
                trial.save()
        except stripe.error.CardError as ex:
            logger.info("stripe card error during stripe customer create: %s", ex)
            raise serializers.ValidationError({"stripe_token": [str(ex)]})
        except stripe.error.StripeError:
            logger.exception("stripe error during stripe customer create")
            raise serializers.ValidationError(
                {"non_field_errors": [_("An error has occurred.  Please try again later.")]}
            )
        return stripe_customer

    def update(self, instance, validated_data):
        if not instance.stripe_id:
            if "stripe_token" in validated_data:
                stripe_customer = self.create_stripe_customer(
                    validated_data.pop("stripe_token"),
                    validated_data.get("billing_interval", instance.billing_interval),
                    instance.facility,
                )
                stripe_subscription = stripe_customer.subscriptions.data[0]
                instance.stripe_id = stripe_subscription.id
                instance.current_period_start = _timestamp_to_utc_datetime(
                    stripe_subscription.current_period_start
                )
                instance.current_period_end = _timestamp_to_utc_datetime(
                    stripe_subscription.current_period_end
                )
                instance.trial_start = (
                    _timestamp_to_utc_datetime(stripe_subscription.trial_start)
                    if stripe_subscription.trial_start
                    else None
                )
                instance.trial_end = (
                    _timestamp_to_utc_datetime(stripe_subscription.trial_end)
                    if stripe_subscription.trial_end
                    else None
                )

        try:
            stripe_subscription = stripe.Subscription.retrieve(instance.stripe_id)
            if (
                "billing_interval" in validated_data
                and instance.billing_interval != validated_data["billing_interval"]
            ):
                stripe_subscription.plan = validated_data["billing_interval"].stripe_id
            if "stripe_token" in validated_data:
                stripe_subscription.source = validated_data.pop("stripe_token")
            stripe_subscription.save()
        except stripe.error.CardError as ex:
            logger.info("stripe card error during subscription update: %s", ex)
            raise serializers.ValidationError({"stripe_token": [str(ex)]})
        except stripe.error.StripeError:
            logger.exception("stripe error during subscription update")
            raise serializers.ValidationError(
                {"non_field_errors": [_("An error has occurred.  Please try again later.")]}
            )

        return super(SubscriptionSerializer, self).update(instance, validated_data)


class SubscriptionTrialSerializer(ModelSerializer):
    stripe_token = serializers.CharField(write_only=True, required=False)
    ebook = serializers.BooleanField(default=False)
    # no_payment is mostly a sanity check to ensure stripe_token wasnt omitted by mistake
    no_payment = serializers.BooleanField(default=False)

    class Meta:
        model = Subscription
        fields = ("billing_interval", "stripe_token", "ebook", "no_payment")

    def validate(self, data):
        facility = self.context["request"].facility
        module = data["billing_interval"].plan.module
        if (
            not data.get("stripe_token", None)
            and not data["no_payment"]
            and module == Plan.Module.staff
        ):
            raise serializers.ValidationError({"stripe_token": _("This field is required.")})

        if facility.subscriptions.filter(billing_interval__plan__module=module).exists():
            raise serializers.ValidationError(
                _("Your facility is ineligible to start a trial subscription.")
            )
        return data

    def create(self, validated_data):
        facility = self.context["request"].facility
        billing_interval = validated_data["billing_interval"]
        if not validated_data["no_payment"]:
            stripe_token = validated_data.get("stripe_token", None)
            if stripe_token:
                FacilityPaymentMethod.objects.update_or_create(
                    facility=facility, defaults={"stripe_token": stripe_token}
                )
        return Subscription.objects.create_trial(
            facility=facility, billing_interval=billing_interval
        )


class SponsorsSerializer(ModelSerializer):
    class Meta:
        model = Sponsor
        fields = ("id", "name", "banner_1", "url_1", "banner_2", "url_2")
