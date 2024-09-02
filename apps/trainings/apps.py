from django.apps import AppConfig


class TrainingsConfig(AppConfig):
    name = "apps.trainings"

    def ready(self):
        from . import signals  # noqa
