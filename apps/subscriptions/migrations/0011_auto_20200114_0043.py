# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-01-14 00:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0142_auto_20200110_0522"),
        ("subscriptions", "0010_auto_20200110_0418"),
    ]

    operations = [
        migrations.RenameModel(old_name="Sponsorship", new_name="Sponsor"),
        migrations.RenameModel(old_name="SponsorshipFacility", new_name="Sponsorship"),
        migrations.RenameField(
            model_name="sponsorship",
            old_name="sponsorship",
            new_name="sponsor",
        ),
        migrations.AddField(
            model_name="sponsor",
            name="date_paid",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="OptedInFacility",
            fields=[],
            options={
                "verbose_name_plural": "Opted in Facilities",
                "proxy": True,
                "indexes": [],
            },
            bases=("trainings.facility",),
        ),
    ]
