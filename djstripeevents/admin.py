from django.contrib import admin

from .models import Event


class EventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "stripe_id",
        "type",
        "created",
    )
    list_filter = (
        "created",
        "type",
    )
    search_fields = ("stripe_id",)
    fields = (
        "stripe_id",
        "type",
        "created",
        "data",
        "pending_webhooks",
        "request",
    )


admin.site.register(Event, EventAdmin)
