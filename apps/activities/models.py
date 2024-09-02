from actstream.models import Action


class Activity(Action):
    class Meta:
        proxy = True
        verbose_name_plural = "activities"
