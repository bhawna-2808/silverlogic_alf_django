from datetime import timedelta

from django.db import models
from django.utils import timezone


class EmployeeManager(models.Manager):
    def get_queryset(self):
        return EmployeeQuerySet(self.model, using=self._db)


class EmployeeQuerySet(models.QuerySet):
    def delete(self):
        self.update(is_active=False)


class TaskManager(models.Manager):
    def get_queryset(self):
        return TaskQuerySet(self.model, using=self._db)

    def bulk_create(*args, **kwargs):
        raise RuntimeError("Bulk creation is not allowed.")


class TaskQuerySet(models.QuerySet):
    def outstanding(self):
        now = timezone.now().date()
        due_date_limit = now + timedelta(days=90)
        return self.filter(due_date__lte=due_date_limit)
