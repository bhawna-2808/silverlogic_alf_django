# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-07-19 15:27


import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ("residents", "0037_auto_20190712_2023"),
        ("facilities", "0009_userinvite_employee"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserResidentAccess",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("is_allowed", models.BooleanField(default=True)),
                (
                    "resident",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_resident_access",
                        to="residents.Resident",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_resident_access",
                        to="facilities.FacilityUser",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "user resident accesses",
            },
        ),
        migrations.AlterUniqueTogether(
            name="userresidentaccess",
            unique_together=set([("user", "resident")]),
        ),
    ]
