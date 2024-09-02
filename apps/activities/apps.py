from django.apps import AppConfig, apps


class ActivityConfig(AppConfig):
    name = "apps.activities"

    def ready(self):
        from actstream import registry

        registry.register(apps.get_model("auth.user"))
        registry.register(apps.get_model("trainings.facility"))
        registry.register(apps.get_model("residents.resident"))
        registry.register(apps.get_model("trainings.employee"))
        registry.register(apps.get_model("subscriptions.subscription"))
