import csv

from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html

from apps.trainings.admin import FacilityAdmin, FacilityDefaultAdmin, FacilityPaymentMethodInline

from .forms import BillingIntervalInlineForm, SubscriptionForm
from .models import (
    BillingInterval,
    FacilityPaymentMethod,
    Invoice,
    InvoiceItem,
    OptedInFacility,
    Plan,
    Sponsor,
    Sponsorship,
    Subscription,
)


class BillingIntervalInline(admin.TabularInline):
    model = BillingInterval
    form = BillingIntervalInlineForm
    fieldsets = ((None, {"fields": ("stripe_id", "amount", "interval", "interval_count")}),)
    readonly_fields = (
        "amount",
        "interval",
        "interval_count",
    )
    extra = 1


class PlanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "module",
        "capacity_limit",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "module",
                    "capacity_limit",
                )
            },
        ),
    )
    inlines = [BillingIntervalInline]


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "facility",
        "plan",
        "billing_interval",
        "status",
    )
    list_filter = (
        "billing_interval__plan",
        "status",
        "facility__bought_ebook",
        "facility__state_facility",
    )
    search_fields = ("facility__name",)
    readonly_fields = ("stripe_link",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "facility",
                    "billing_interval",
                    "status",
                    ("current_period_start", "current_period_end"),
                )
            },
        ),
        ("Trial", {"fields": (("trial_start", "trial_end"),)}),
        ("Stripe", {"fields": ("stripe_id", "stripe_link")}),
    )
    form = SubscriptionForm

    def plan(self, obj):
        return obj.billing_interval.plan

    plan.admin_order_field = "billing_interval__plan"

    def stripe_link(self, obj):
        if obj.stripe_id:
            url = "https://dashboard.stripe.com/subscriptions/%s" % obj.stripe_id
            return '<a href="%s">%s</a>' % (url, "View on stripe")
        return "No stripe id"

    stripe_link.allow_tags = True


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    fields = (
        "description",
        "amount",
    )


class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "facility",
        "subtotal",
        "tax",
        "total",
        "is_attempted",
        "is_paid",
        "datetime",
    )
    list_filter = (
        "is_attempted",
        "is_paid",
        "datetime",
    )
    search_fields = ("subscription__facility__name",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "subscription",
                    "amount_due",
                    "subtotal",
                    "tax",
                    "total",
                    ("period_start", "period_end"),
                    "receipt_number",
                    ("is_attempted", "attempt_count"),
                    "is_paid",
                    "is_closed",
                    "datetime",
                )
            },
        ),
        (
            "Stripe",
            {
                "fields": (
                    "stripe_id",
                    "stripe_charge_id",
                    "stripe_subscription_id",
                    "stripe_customer_id",
                )
            },
        ),
    )
    inlines = [InvoiceItemInline]

    def facility(self, obj):
        return obj.subscription.facility

    facility.admin_order_field = "subscription__facility"


class FacilityPaymentMethodAdmin(admin.ModelAdmin):
    model = FacilityPaymentMethod
    list_display = (
        "id",
        "facility",
    )
    fields = (
        "facility",
        "stripe_token",
    )


class SponsorshipInline(admin.TabularInline):
    model = Sponsorship
    raw_id_fields = ("facility",)
    extra = 1


class SponsorStateInline(admin.TabularInline):
    model = Sponsor.state.through
    extra = 1


class SponsorAdmin(admin.ModelAdmin):
    change_form_template = "subscriptions/admin/subscriptions/sponsor/change_form.html"
    model = Sponsor
    list_display = (
        "id",
        "name",
    )
    inlines = [SponsorshipInline, SponsorStateInline]
    list_filter = ("state",)


class OptedInFacilityAdmin(FacilityAdmin):
    list_display = ("name", "opted_in_sponsorship_date", "sponsors")
    inlines = [FacilityDefaultAdmin, FacilityPaymentMethodInline, SponsorshipInline]
    search_fields = ("name", "sponsorships__sponsor__name")
    list_filter = ("sponsorships__sponsor__name", "state_facility")
    actions = ["export_csv"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(opted_in_sponsorship_date__isnull=False, sponsored_access=True)

    def sponsors(self, obj):
        output = ""
        for e in obj.sponsorships.all():
            url = reverse(
                f"admin:{e.sponsor._meta.app_label}_{e.sponsor._meta.model_name}_change",
                args=[e.sponsor.pk],
            )
            output += format_html('<a href="{url}">{name}</a>', url=url, name=e.sponsor.name) + ", "
        return format_html(output[:-2])

    def _get_csv_headers(self):
        facility_headers = [
            "Facility name",
            "Capacity",
        ]
        sponsorship_headers = [
            "Sponsor name",
            "Amount Paid",
            "Date Paid",
            "Start Date",
            "End Date",
            "Zip Code",
            "County",
            "Notes",
        ]
        subscription_headers = [
            "Last Staff Subscription Type",
            "Last Staff Subscription Price",
            "Last Staff Subscription Date Paid",
        ]
        return (facility_headers, sponsorship_headers, subscription_headers)

    def _get_csv_sponsorship_fields(self, sponsorship):
        sponsor = sponsorship.sponsor
        return [
            sponsor.name,
            sponsor.amount_paid,
            sponsor.date_paid,
            sponsorship.start_date,
            sponsorship.end_date,
            sponsor.zip_code,
            sponsor.county,
            sponsorship.notes,
        ]

    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="facilities.csv"'

        writer = csv.writer(response)
        (
            facility_headers,
            sponsorship_headers,
            subscription_headers,
        ) = self._get_csv_headers()
        writer.writerow(
            [
                *facility_headers,
                *sponsorship_headers,
                *subscription_headers,
            ]
        )
        for facility in queryset:
            facility_fields = [
                facility.name,
                facility.capacity,
            ]
            last_subscription = (
                facility.subscriptions.filter(billing_interval__plan__module=Plan.Module.staff)
                .is_active()
                .last()
            )
            subscription_fields = [None for i in range(len(subscription_headers))]
            if last_subscription:
                subscription_fields = [
                    last_subscription.billing_interval.interval,
                    last_subscription.billing_interval.amount,
                    last_subscription.current_period_start,
                ]
            if facility.sponsorships.exists():
                for sponsorship in facility.sponsorships.all():
                    writer.writerow(
                        [
                            *facility_fields,
                            *self._get_csv_sponsorship_fields(sponsorship),
                            *subscription_fields,
                        ]
                    )
            else:
                writer.writerow(
                    [
                        *facility_fields,
                        *[None for i in range(len(sponsorship_headers))],
                        *subscription_fields,
                    ]
                )

        return response


admin.site.register(Plan, PlanAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(FacilityPaymentMethod, FacilityPaymentMethodAdmin)
admin.site.register(Sponsor, SponsorAdmin)
admin.site.register(OptedInFacility, OptedInFacilityAdmin)
