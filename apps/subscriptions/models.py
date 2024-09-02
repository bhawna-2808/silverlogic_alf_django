import datetime
import logging
from decimal import Decimal

from django.contrib.gis.db import models as gis_models
from django.contrib.gis.db.models import Case, F, IntegerField, Value, When
from django.contrib.gis.db.models.functions import Distance
from django.db import models
from django.db.models import Count, ExpressionWrapper
from django.dispatch import receiver
from django.template.defaultfilters import pluralize
from django.utils.translation import gettext_lazy as _

import stripe
from django_fsm import FSMField, transition
from localflavor.us.models import USZipCodeField
from model_utils import Choices
from model_utils.models import TimeStampedModel

from apps.base.geocoder import get_geolocation_point
from apps.base.models import random_name_in
from apps.trainings.models import Facility
from djstripeevents.signals import event_received

from .managers import SubscriptionManager

logger = logging.getLogger(__name__)


class Plan(models.Model):
    Module = Choices(
        ("resident", _("Resident")),
        ("staff", _("Staff")),
        ("trainings", _("Trainings")),
    )

    name = models.CharField(max_length=100)
    module = models.CharField(choices=Module, max_length=50)

    # Resident module fields
    capacity_limit = models.PositiveIntegerField(blank=True, null=True, help_text=_("Inclusive"))

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Plan: {}>".format(self.pk)


class BillingInterval(models.Model):
    Interval = Choices(
        ("day", _("Day")),
        ("week", _("Week")),
        ("month", _("Month")),
        ("year", _("Year")),
    )

    stripe_id = models.CharField(max_length=255)
    plan = models.ForeignKey("Plan", related_name="billing_intervals", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    interval = models.CharField(choices=Interval, max_length=25)
    interval_count = models.PositiveIntegerField(
        help_text=_("The number of intervals between each subscription billing.")
    )

    class Meta:
        ordering = ["amount"]
        unique_together = [
            ["plan", "interval", "interval_count"],
        ]

    def __str__(self):
        return "${} every {}".format(
            self.amount,
            pluralize(
                self.interval_count,
                "{0},{1} {0}s".format(self.interval, self.interval_count),
            ),
        )

    def __repr__(self):
        return "<BillingInterval: {}>".format(self.pk)


class FacilityPaymentMethod(models.Model):
    stripe_token = models.CharField(max_length=255, blank=True)
    facility = models.OneToOneField(
        "trainings.Facility", related_name="payment_method", on_delete=models.CASCADE
    )


class Subscription(TimeStampedModel):
    Status = Choices(
        ("trialing", _("Trialing")),
        ("trial_expired", _("Trial Expired")),
        ("active", _("Active")),
        (
            "past_due",
            _("Past Due"),
        ),  # Charging a payment has failed, stripe will retry.
        (
            "canceled",
            _("Canceled"),
        ),  # user has canceled or stripe payment retries failed too many times.
        # user has canceled their subscription but it remains active until the end of the billing cycle.
        ("pending_cancel", _("Pending Cancellation")),
    )

    stripe_id = models.CharField(max_length=255, blank=True)
    facility = models.ForeignKey(
        "trainings.Facility", related_name="subscriptions", on_delete=models.CASCADE
    )
    billing_interval = models.ForeignKey(
        "BillingInterval", related_name="subscriptions", on_delete=models.CASCADE
    )
    status = FSMField(choices=Status, default=Status.active)

    current_period_start = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)

    trial_start = models.DateTimeField(blank=True, null=True)
    trial_end = models.DateTimeField(blank=True, null=True)

    objects = SubscriptionManager()

    def __str__(self):
        return "{} - {}: {} - {}".format(
            self.facility,
            self.billing_interval.plan,
            self.billing_interval,
            self.Status[self.status],
        )

    def __repr__(self):
        return "<Subscription: {}>".format(self.pk)

    @transition(field=status, source=(Status.trialing, Status.active, Status.past_due))
    def cancel(self):
        if self.status == self.Status.trialing:
            self.cancel_trial()
        else:
            self.cancel_non_trial()

    @transition(field=status, source=Status.trialing, target=Status.canceled)
    def cancel_trial(self):
        pass

    @transition(field=status, source=Status.trialing, target=Status.trial_expired)
    def trial_expired(self):
        pass

    @transition(
        field=status,
        source=(Status.active, Status.past_due),
        target=Status.pending_cancel,
    )
    def cancel_non_trial(self):
        stripe_subscription = stripe.Subscription.retrieve(self.stripe_id)
        stripe_subscription.delete(at_period_end=True)

    @transition(
        field=status,
        source=(Status.active, Status.past_due, Status.pending_cancel),
        target=Status.canceled,
    )
    def cancel_by_stripe(self):
        pass


class Invoice(models.Model):
    subscription = models.ForeignKey("Subscription", on_delete=models.CASCADE)
    currency = models.CharField(max_length=3)
    amount_due = models.DecimalField(max_digits=11, decimal_places=2)
    subtotal = models.DecimalField(max_digits=11, decimal_places=2)
    tax = models.DecimalField(max_digits=11, decimal_places=2)
    total = models.DecimalField(max_digits=11, decimal_places=2)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    receipt_number = models.CharField(max_length=255, blank=True)
    is_attempted = models.BooleanField()
    attempt_count = models.PositiveIntegerField(
        help_text=_("Number of payment attempts made for this invoice.")
    )
    is_paid = models.BooleanField()
    is_closed = models.BooleanField()
    datetime = models.DateTimeField(blank=True, null=True)

    stripe_id = models.CharField(max_length=255, unique=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255)
    stripe_customer_id = models.CharField(max_length=255)

    def __str__(self):
        return "${:,.2f}".format(self.total)

    def __repr__(self):
        return "<Invoice: {}>".format(self.pk)


class InvoiceItem(models.Model):
    invoice = models.ForeignKey("Invoice", on_delete=models.CASCADE)
    currency = models.CharField(max_length=3)
    amount = models.DecimalField(max_digits=11, decimal_places=2)
    description = models.CharField(max_length=255)

    stripe_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return "{} ${:,.2f}".format(self.description, self.amount)

    def __repr__(self):
        return "<InvoiceItem: {}>".format(self.pk)


class Sponsorship(TimeStampedModel):
    facility = models.ForeignKey(
        "trainings.Facility", related_name="sponsorships", on_delete=models.CASCADE
    )
    sponsor = models.ForeignKey(
        "subscriptions.Sponsor", related_name="sponsorhips", on_delete=models.CASCADE
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Sponsorship: {self.sponsor} - {self.facility}"


class Sponsor(TimeStampedModel):
    name = models.CharField(max_length=255, verbose_name="Sponsor Name")
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2)
    date_paid = models.DateField(null=True, blank=True)
    zip_code = USZipCodeField()
    county = models.CharField(max_length=255)
    point = gis_models.PointField(blank=True, null=True)

    banner_1 = models.ImageField(
        blank=True,
        null=True,
        upload_to=random_name_in("trainings/sponsorships/banner_1"),
    )
    url_1 = models.URLField(blank=True)
    banner_2 = models.ImageField(
        blank=True,
        null=True,
        upload_to=random_name_in("trainings/sponsorships/banner_2"),
    )
    url_2 = models.URLField(blank=True)

    state = models.ManyToManyField(
        "alfdirectory.State",
        blank=True,
        through="trainings.SponsorState",
        related_name="sponsors_state",
    )

    def __str__(self):
        return f"Sponsor: {self.name}"

    @property
    def geolocation(self):
        if self.point:
            return self.point

        point = get_geolocation_point(self.zip_code)

        if point:
            # Avoid post save signal
            Sponsor.objects.filter(id=self.id).update(point=point)
        return point

    @property
    def nearby_facilities(self):
        qs = (
            Facility.objects.annotate(
                sponsor_count=Count("sponsorships__sponsor", distinct=True),
                active_residents=Count(
                    Case(
                        When(residents__is_active=True, then=Value(1)),
                        output_field=IntegerField(),
                    )
                ),
                distance=Distance("point", self.point),
                distance_mi=ExpressionWrapper(
                    F("distance") * Value(0.000621371), output_field=IntegerField()
                ),
                same_county=Case(
                    When(
                        address_county=Value(self.county),
                        then=Value(1),
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
            )
            .prefetch_related("questions")
            .order_by("-same_county", "distance")
            .all()
        )
        return qs


@receiver(event_received)
def handle_stripe_event_received(sender, event, **kwargs):
    if event.type == event.Type.customer__subscription__deleted:
        handle_subscription_deleted(event)
    elif event.type == event.Type.customer__subscription__updated:
        handle_subscription_updated(event)
    elif event.type in (event.Type.invoice__created, event.Type.invoice__updated):
        handle_invoice_created_or_updated(event)


def handle_subscription_deleted(stripe_event):
    stripe_id = stripe_event.data["object"]["id"]
    try:
        subscription = Subscription.objects.get(stripe_id=stripe_id)
    except Subscription.DoesNotExist:
        logger.warning(
            "received webhook %s (%s) for subscription that does not exist: %s",
            stripe_event.stripe_id,
            stripe_event.type,
            stripe_id,
        )
    else:
        subscription.cancel_by_stripe()
        subscription.save()


def handle_subscription_updated(stripe_event):
    stripe_id = stripe_event.data["object"]["id"]
    try:
        subscription = Subscription.objects.get(stripe_id=stripe_id)
    except Subscription.DoesNotExist:
        logger.warning(
            "received webhook %s (%s) for subscription that does not exist: %s",
            stripe_event.stripe_id,
            stripe_event.type,
            stripe_id,
        )
    else:
        stripe_subscription = stripe_event.data["object"]
        if stripe_subscription["status"] == Subscription.Status.active:
            # We use an additional status `pending_cancel` where stripe uses a boolean.
            if not stripe_subscription["cancel_at_period_end"]:
                subscription.status = stripe_subscription["status"]
        elif stripe_subscription["status"] == Subscription.Status.past_due:
            subscription.status = stripe_subscription["status"]
        elif stripe_subscription["status"] == Subscription.Status.cancel:
            subscription.status = stripe_subscription["status"]

        subscription.current_period_start = datetime.datetime.utcfromtimestamp(
            stripe_subscription["current_period_start"]
        )
        subscription.current_period_end = datetime.datetime.utcfromtimestamp(
            stripe_subscription["current_period_end"]
        )
        subscription.save()


def handle_invoice_created_or_updated(stripe_event):
    stripe_invoice = stripe_event.data["object"]
    try:
        invoice = Invoice.objects.get(stripe_id=stripe_invoice["id"])
    except Invoice.DoesNotExist:
        invoice = Invoice(stripe_id=stripe_invoice["id"])
        try:
            invoice.subscription = Subscription.objects.get(
                stripe_id=stripe_invoice["subscription"]
            )
        except Subscription.DoesNotExist:
            logger.warning(
                "received webhook %s (%s) for subscription that does not exist: %s",
                stripe_event.stripe_id,
                stripe_event.type,
                stripe_invoice["subscription"],
            )
            return

    invoice.stripe_charge_id = stripe_invoice["charge"] or ""
    invoice.stripe_subscription_id = stripe_invoice["subscription"]
    invoice.stripe_customer_id = stripe_invoice["customer"]
    invoice.currency = stripe_invoice["currency"]
    invoice.amount_due = Decimal(stripe_invoice["amount_due"] / 100)
    invoice.subtotal = Decimal(stripe_invoice["subtotal"] / 100)
    invoice.tax = Decimal(stripe_invoice["tax"] / 100) if stripe_invoice["tax"] else 0
    invoice.total = Decimal(stripe_invoice["total"] / 100)
    invoice.period_start = datetime.datetime.utcfromtimestamp(stripe_invoice["period_start"])
    invoice.period_end = datetime.datetime.utcfromtimestamp(stripe_invoice["period_end"])
    invoice.receipt_number = stripe_invoice["receipt_number"] or ""
    invoice.is_attempted = stripe_invoice["attempted"]
    invoice.attempt_count = stripe_invoice["attempt_count"]
    invoice.is_paid = stripe_invoice["paid"]
    invoice.is_closed = stripe_invoice["closed"]
    invoice.datetime = (
        datetime.datetime.utcfromtimestamp(stripe_invoice["date"])
        if stripe_invoice["date"]
        else None
    )
    invoice.save()

    for line in stripe_invoice["lines"]["data"]:
        try:
            invoice_item = InvoiceItem.objects.get(stripe_id=line["id"])
        except InvoiceItem.DoesNotExist:
            invoice_item = InvoiceItem(stripe_id=line["id"])
            invoice_item.invoice = invoice

        invoice_item.currency = line["currency"]
        invoice_item.amount = Decimal(line["amount"] / 100)
        invoice_item.description = line["description"] or ""
        invoice_item.save()


class OptedInFacility(Facility):
    class Meta:
        verbose_name_plural = "Opted in Facilities"
        proxy = True
