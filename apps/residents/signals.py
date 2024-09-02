from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.residents.models import Resident, ResidentBedHold
from apps.residents.tasks import send_ltc_status_notification


@receiver(post_save, sender=Resident)
def on_save_resident(sender, instance, created, **kwargs):
    if instance.long_term_care_provider not in ["Simply", "Sunshine"]:
        return

    amends = []
    if instance.tracker.has_changed("long_term_care_provider"):
        amends.append("enrollment")
    if created:
        amends.append("admission")
    if instance.tracker.has_changed("date_of_discharge"):
        amends.append("discharge")

    if amends:
        send_ltc_status_notification.delay(instance.id, amends)


@receiver(post_save, sender=ResidentBedHold)
def on_save_resident_bed_hold(sender, instance, created, **kwargs):
    send_ltc_status_notification.delay(instance.id, ["bed_hold"])
