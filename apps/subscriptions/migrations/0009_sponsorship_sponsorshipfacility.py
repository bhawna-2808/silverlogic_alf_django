# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-01-09 18:11
from __future__ import unicode_literals

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import localflavor.us.models
import model_utils.fields

import apps.base.models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0141_auto_20200109_1811"),
        ("subscriptions", "0008_auto_20191114_2331"),
    ]

    operations = [
        migrations.CreateModel(
            name="Sponsorship",
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
                ("name", models.CharField(max_length=255)),
                ("amount_paid", models.DecimalField(decimal_places=2, max_digits=8)),
                ("zip_code", localflavor.us.models.USZipCodeField(max_length=10)),
                ("county", models.CharField(max_length=255)),
                (
                    "banner_1",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=apps.base.models.random_name_in(
                            "trainings/sponsorships/banner_1"
                        ),
                    ),
                ),
                ("url_1", models.URLField(blank=True)),
                (
                    "banner_2",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=apps.base.models.random_name_in(
                            "trainings/sponsorships/banner_2"
                        ),
                    ),
                ),
                ("url_2", models.URLField(blank=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="SponsorshipFacility",
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
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                (
                    "facility",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sponsorships",
                        to="trainings.Facility",
                    ),
                ),
                (
                    "sponsorship",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="facilities",
                        to="subscriptions.Sponsorship",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
