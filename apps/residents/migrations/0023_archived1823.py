# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-03-16 18:56


import django.db.models.deletion
from django.db import migrations, models

import apps.base.models


class Migration(migrations.Migration):

    dependencies = [
        ("residents", "0022_auto_20170310_1636"),
    ]

    operations = [
        migrations.CreateModel(
            name="Archived1823",
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
                ("date_signed", models.DateField()),
                ("date_archived", models.DateField(auto_now_add=True)),
                (
                    "data_archived",
                    models.FileField(
                        upload_to=apps.base.models.random_name_in("residents/archived1823s")
                    ),
                ),
                (
                    "resident",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="residents.Resident",
                    ),
                ),
            ],
            options={
                "ordering": ["-date_signed", "-id"],
            },
        ),
    ]
