# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-12-23 16:31


from django.db import migrations

import apps.base.models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0135_auto_20191205_1243"),
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
