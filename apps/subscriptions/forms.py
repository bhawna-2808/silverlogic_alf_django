from django.forms import ModelChoiceField, ModelForm, ValidationError
from django.utils.translation import gettext_lazy as _

import stripe

from apps.trainings.models import Facility

from .models import BillingInterval, Subscription


class BillingIntervalInlineForm(ModelForm):
    class Meta:
        model = BillingInterval
        fields = ("stripe_id", "amount", "interval", "interval_count")
        readonly_fields = (
            "amount",
            "interval",
            "interval_count",
        )

    def clean_stripe_id(self):
        stripe_id = self.cleaned_data.get("stripe_id")

        qs = BillingInterval.objects.filter(stripe_id=stripe_id)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(_("That stripe id is already in use."))

        for stripe_plan in stripe.Plan.list():
            if stripe_plan.id == stripe_id:
                self.stripe_plan = stripe_plan
                break
        else:
            raise ValidationError(_("Could not find a stripe plan with the given id."))

        return stripe_id

    def save(self, commit=True):
        billing_frequency = super(BillingIntervalInlineForm, self).save(commit=False)
        billing_frequency.amount = self.stripe_plan.amount / 100.0
        billing_frequency.interval = self.stripe_plan.interval
        billing_frequency.interval_count = self.stripe_plan.interval_count
        if commit:
            billing_frequency.save()
        return billing_frequency


class SubscriptionForm(ModelForm):
    facility = ModelChoiceField(queryset=Facility.objects.order_by("name"))

    class Meta:
        model = Subscription
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(SubscriptionForm, self).__init__(*args, **kwargs)
        self.fields["billing_interval"].label_from_instance = lambda x: "{}: {}".format(
            x.plan, str(x)
        )
