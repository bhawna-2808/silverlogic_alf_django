from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.subscriptions.models import Sponsor


@receiver(post_save, sender=Sponsor)
def create_default_instance_for_facility(sender, instance, **kwargs):
    if instance.point is None:
        instance.geolocation
