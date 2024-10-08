# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-01-09 18:11
from __future__ import unicode_literals

from django.db import migrations

import apps.base.models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0140_auto_20200108_1739"),
    ]

    operations = [
        migrations.AlterField(
            model_name="employee",
            name="phone_number",
            field=apps.base.models.UsPhoneNumberField(
                blank=True,
                max_length=50,
                validators=[
                    apps.base.models.validate_us_phone_number,
                    apps.base.models.validate_us_phone_number,
                    apps.base.models.validate_us_phone_number,
                ],
            ),
        ),
    ]
