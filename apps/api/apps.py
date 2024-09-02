from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = "apps.api"

    def ready(self):
        from . import monkeypatch  # noqa
