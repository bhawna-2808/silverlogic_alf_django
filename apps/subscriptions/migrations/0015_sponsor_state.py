# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2022-03-24 13:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("alfdirectory", "0003_auto_20220324_1333"),
        ("trainings", "0160_auto_20220324_1333"),
        ("subscriptions", "0014_sponsor_point"),
    ]

    operations = [
        migrations.AddField(
            model_name="sponsor",
            name="state",
            field=models.ManyToManyField(
                blank=True,
                related_name="sponsors_state",
                through="trainings.SponsorState",
                to="alfdirectory.State",
            ),
        ),
    ]
