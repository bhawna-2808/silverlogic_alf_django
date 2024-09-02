from expander import ExpanderSerializerMixin

from apps.subscriptions.models import BillingInterval, Plan

from ..serializers import ModelSerializer


class PlanNoBillingIntervalSerializer(ModelSerializer):
    class Meta:
        model = Plan
        fields = (
            "id",
            "name",
            "module",
            "capacity_limit",
        )


class BillingIntervalSerializer(ExpanderSerializerMixin, ModelSerializer):
    class Meta:
        model = BillingInterval
        fields = (
            "id",
            "amount",
            "interval",
            "interval_count",
        )
        expandable_fields = {
            "plan": PlanNoBillingIntervalSerializer,
        }


class PlanSerializer(ModelSerializer):
    billing_intervals = BillingIntervalSerializer(many=True)

    class Meta:
        model = Plan
        fields = (
            "id",
            "name",
            "module",
            "capacity_limit",
            "billing_intervals",
        )
