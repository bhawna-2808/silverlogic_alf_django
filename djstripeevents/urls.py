from django.urls import re_path

from .views import StripeWebhookView

urlpatterns = [
    re_path(r"^webhook/$", StripeWebhookView.as_view(), name="stripe-webhook"),
]
