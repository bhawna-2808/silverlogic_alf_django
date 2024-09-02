# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models

import localflavor.us.models

import apps.base.models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0071_auto_20160403_1442"),
    ]

    operations = [
        migrations.CreateModel(
            name="Resident",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("first_name", models.CharField(max_length=255)),
                ("last_name", models.CharField(max_length=255)),
                (
                    "avatar",
                    models.ImageField(
                        null=True,
                        upload_to=apps.base.models.random_name_in("residents/resident-avatars"),
                        blank=True,
                    ),
                ),
                ("date_of_birth", models.DateField(null=True, blank=True)),
                (
                    "sex",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        choices=[("m", "Male"), ("f", "Female"), ("other", "Other")],
                    ),
                ),
                (
                    "marital_status",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        choices=[
                            ("single", "Single"),
                            ("married", "Married"),
                            ("divorced", "Divorced"),
                            ("widowed", "Widowed"),
                        ],
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("room_number", models.CharField(max_length=255, blank=True)),
                ("bed", models.CharField(max_length=255, blank=True)),
                ("religion", models.CharField(max_length=255, blank=True)),
                (
                    "ssn",
                    localflavor.us.models.USSocialSecurityNumberField(max_length=11, blank=True),
                ),
                ("date_of_admission", models.DateField(null=True, blank=True)),
                ("admitted_from", models.CharField(max_length=255, blank=True)),
                ("date_of_discharge", models.DateField(null=True, blank=True)),
                ("discharged_to", models.CharField(max_length=255, blank=True)),
                ("reason_for_discharge", models.CharField(max_length=255, blank=True)),
                ("notes", models.TextField(blank=True)),
                (
                    "facility",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="residents",
                        to="trainings.Facility",
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="ResidentRace",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "race",
                    models.CharField(
                        max_length=255,
                        choices=[
                            ("white", "White"),
                            ("black", "Black or African American"),
                            ("latino", "Hispanic/Latino"),
                            ("asian", "Asian"),
                            ("other", "Other"),
                        ],
                    ),
                ),
                (
                    "other_text",
                    models.CharField(help_text="When race is other.", max_length=255, blank=True),
                ),
                (
                    "resident",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="races",
                        to="residents.Resident",
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
