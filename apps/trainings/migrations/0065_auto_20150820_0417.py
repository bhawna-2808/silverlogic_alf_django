# -*- coding: utf-8 -*-


from django.db import migrations


def create_default_for_facilities(apps, schema_editor):
    Facility = apps.get_model("trainings", "Facility")
    FacilityDefault = apps.get_model("trainings", "FacilityDefault")

    for facility in Facility.objects.all():
        if not hasattr(facility, "default"):
            FacilityDefault.objects.create(facility=facility)


def remove_default_from_facilities(apps, schema_editor):
    Facility = apps.get_model("trainings", "Facility")

    for facility in Facility.objects.all():
        if facility.default:
            facility.default.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0064_auto_20150813_1916"),
    ]

    operations = [
        migrations.RunPython(create_default_for_facilities, remove_default_from_facilities),
    ]
