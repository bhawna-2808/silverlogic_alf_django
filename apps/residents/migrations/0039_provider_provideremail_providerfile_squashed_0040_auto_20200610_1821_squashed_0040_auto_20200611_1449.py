# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-06-11 14:50
from __future__ import unicode_literals

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import model_utils.fields

import apps.residents.utils


class Migration(migrations.Migration):

    replaces = [
        (
            "residents",
            "0039_provider_provideremail_providerfile_squashed_0040_auto_20200610_1821",
        ),
        ("residents", "0040_auto_20200611_1449"),
    ]

    dependencies = [
        ("residents", "0038_remove_resident_npi"),
    ]

    operations = [
        migrations.CreateModel(
            name="Provider",
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
                    "name",
                    models.CharField(max_length=255, unique=True, verbose_name="LTC Provider name"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ProviderEmail",
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
                ("email", models.EmailField(max_length=254)),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="residents.Provider",
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
            ],
        ),
        migrations.CreateModel(
            name="ProviderFile",
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
                (
                    "file",
                    models.FileField(upload_to=apps.residents.utils.provider_file_path),
                ),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="residents.Provider",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="provider",
            name="contact",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="provider",
            name="position",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="LTC provider position",
            ),
        ),
        migrations.AddField(
            model_name="provider",
            name="created",
            field=model_utils.fields.AutoCreatedField(
                default=django.utils.timezone.now,
                editable=False,
                verbose_name="created",
            ),
        ),
        migrations.AddField(
            model_name="provider",
            name="modified",
            field=model_utils.fields.AutoLastModifiedField(
                default=django.utils.timezone.now,
                editable=False,
                verbose_name="modified",
            ),
        ),
    ]
