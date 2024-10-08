# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-02-12 17:23


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0098_tasktype_required_after_task_type"),
        ("subscriptions", "0006_plan_module"),
    ]

    operations = [
        migrations.CreateModel(
            name="FacilityPaymentMethod",
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
                ("stripe_token", models.CharField(blank=True, max_length=255)),
                (
                    "facility",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payment_method",
                        to="trainings.Facility",
                    ),
                ),
            ],
        ),
    ]
