# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-22 18:35


import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import django_fsm
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0080_auto_20160615_1652"),
        ("subscriptions", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Subscription",
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
                ("stripe_id", models.CharField(blank=True, max_length=255)),
                (
                    "status",
                    django_fsm.FSMField(
                        choices=[
                            ("active", "Active"),
                            ("past_due", "Past Due"),
                            ("canceled", "Canceled"),
                            ("pending_cancel", "Pending Cancellation"),
                        ],
                        default="active",
                        max_length=50,
                    ),
                ),
                (
                    "billing_interval",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscriptions",
                        to="subscriptions.BillingInterval",
                    ),
                ),
                (
                    "facility",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscriptions",
                        to="trainings.Facility",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
