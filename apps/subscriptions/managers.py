from datetime import timedelta

from django.db import models
from django.db.models import Q
from django.db.models.functions import Now
from django.utils import timezone


class SubscriptionManager(models.Manager):
    def create_trial(self, facility, billing_interval):
        subscription = self.model(facility=facility, billing_interval=billing_interval)
        subscription.status = self.model.Status.trialing
        subscription.trial_start = timezone.now()
        subscription.trial_end = subscription.trial_start + timedelta(days=30)
        subscription.save()
        return subscription


class SubscriptionQuerySet(models.QuerySet):
    def is_active(self):
        from .models import Plan

        return self.filter(
            Q(billing_interval__plan__module=Plan.Module.staff)
            | Q(billing_interval__plan__module=Plan.Module.trainings)
            | Q(billing_interval__plan__module=Plan.Module.resident)
            & Q(facility__businessagreement__isnull=False)
        ).filter(
            Q(status__in=[self.model.Status.active, self.model.Status.pending_cancel])
            | Q(status=self.model.Status.trialing, trial_end__gte=Now())
        )

    def current(self):
        return self.exclude(
            Q(status=self.model.Status.canceled) | Q(status=self.model.Status.trial_expired)
        )


SubscriptionManager = SubscriptionManager.from_queryset(SubscriptionQuerySet)
