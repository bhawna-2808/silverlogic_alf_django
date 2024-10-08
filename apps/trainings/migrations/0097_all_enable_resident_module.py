# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2018-10-12 19:14


from django.db import migrations


def enable(apps, schema_migration):
    Facility = apps.get_model("trainings.Facility")
    Facility.objects.all().update(is_resident_module_enabled=True)


class Migration(migrations.Migration):
    dependencies = [
        ("trainings", "0096_auto_20181012_1912"),
    ]

    operations = [
        migrations.RunPython(enable, migrations.RunPython.noop),
    ]
