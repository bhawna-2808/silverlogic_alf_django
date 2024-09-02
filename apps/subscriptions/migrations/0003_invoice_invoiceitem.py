# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-23 20:23


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0002_subscription"),
    ]

    operations = [
        migrations.CreateModel(
            name="Invoice",
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
                ("stripe_id", models.CharField(max_length=255, unique=True)),
                ("stripe_charge_id", models.CharField(blank=True, max_length=255)),
                ("stripe_subscription_id", models.CharField(max_length=255)),
                ("stripe_customer_id", models.CharField(max_length=255)),
                ("currency", models.CharField(max_length=3)),
                ("amount_due", models.DecimalField(decimal_places=2, max_digits=11)),
                ("subtotal", models.DecimalField(decimal_places=2, max_digits=11)),
                ("tax", models.DecimalField(decimal_places=2, max_digits=11)),
                ("total", models.DecimalField(decimal_places=2, max_digits=11)),
                ("period_start", models.DateTimeField()),
                ("period_end", models.DateTimeField()),
                ("receipt_number", models.CharField(max_length=255)),
                ("is_attempted", models.BooleanField()),
                (
                    "attempt_count",
                    models.PositiveIntegerField(
                        help_text="Number of payment attempts made for this invoice."
                    ),
                ),
                ("is_paid", models.BooleanField()),
                ("is_closed", models.BooleanField()),
                ("datetime", models.DateTimeField(blank=True, null=True)),
                (
                    "subscription",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="subscriptions.Subscription",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="InvoiceItem",
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
                ("stripe_id", models.CharField(max_length=255, unique=True)),
                ("currency", models.CharField(max_length=3)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=11)),
                ("description", models.CharField(max_length=255)),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="subscriptions.Invoice",
                    ),
                ),
            ],
        ),
    ]
