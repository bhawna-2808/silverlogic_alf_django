from django.apps import AppConfig


class ResidentsConfig(AppConfig):
    name = "apps.residents"

    def ready(self):
        from . import signals  # noqa
