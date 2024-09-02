from django.db import models
from django.db.models import F


class FacilityManager(models.Manager):
    def get_queryset(self):
        return models.QuerySet(self.model, using=self._db).annotate(
            _capacity=F("oss_beds") + F("private_beds")
        )
