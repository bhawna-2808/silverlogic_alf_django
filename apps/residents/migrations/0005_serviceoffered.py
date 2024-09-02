# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("residents", "0004_auto_20160518_1120"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServiceOffered",
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
                ("need_identified", models.CharField(max_length=100)),
                ("service_needed", models.CharField(max_length=100)),
                ("frequency_and_duration", models.CharField(max_length=100)),
                ("service_provider_name", models.CharField(max_length=100)),
                ("date_service_began", models.DateField()),
                (
                    "resident",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="services_offered",
                        to="residents.Resident",
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
