# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-03-30 14:26


from django.db import migrations


def fill_medication_fields(apps, schema_editor):
    Resident = apps.get_model("residents", "Resident")
    for resident in Resident.objects.all():
        resident.is_able_to_administer_without_assistance = (
            not resident.requires_help_taking_medication
        )
        resident.requires_help_taking_medication = (
            resident.requires_help_with_self_administered_medication
            or resident.requires_medication_administration
        )
        resident.save()


class Migration(migrations.Migration):
    dependencies = [
        ("residents", "0024_auto_20170329_1958"),
    ]

    operations = [
        migrations.RunPython(fill_medication_fields),
    ]
