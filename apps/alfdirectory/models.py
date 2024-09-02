from django.db import models

from localflavor.us.us_states import US_STATES
from model_utils.models import TimeStampedModel

from .managers import FacilityManager


class Facility(models.Model):
    name = models.CharField(max_length=255)
    license_number = models.CharField(max_length=255)
    oss_beds = models.PositiveIntegerField()
    private_beds = models.PositiveIntegerField()
    state = models.ForeignKey(
        "State",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="alfdirectory_facilities",
    )

    objects = FacilityManager()

    class Meta:
        verbose_name_plural = "facilities"

    @property
    def capacity(self):
        if getattr(self, "_capacity", None) is not None:
            return self._capacity
        return self.oss_beds + self.private_beds

    def __str__(self):
        return "{} - License #{}".format(self.name, self.license_number)

    def __repr__(self):
        return "<Facility id={}, license#={}>".format(self.pk, self.license_number)


class State(TimeStampedModel):
    state = models.CharField(choices=US_STATES, unique=True, max_length=255)

    def __str__(self):
        return f"{self.get_state_display()}"
