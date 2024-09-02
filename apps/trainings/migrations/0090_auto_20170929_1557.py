# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-09-29 15:57


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0089_auto_20170804_1813"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomTaskType",
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
                ("name", models.TextField()),
                ("description", models.TextField()),
                ("is_training", models.BooleanField(default=False)),
                ("is_one_off", models.BooleanField(default=False)),
                ("required_within", models.DurationField()),
                ("validity_period", models.DurationField()),
                ("rule", models.TextField(blank=True)),
                ("is_request", models.BooleanField(default=True)),
                (
                    "facility",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="trainings.Facility",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CustomTaskTypePrerequisite",
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
                    "custom_task_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="prerequisites",
                        to="trainings.CustomTaskType",
                    ),
                ),
                (
                    "prerequisite",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="trainings.TaskType",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CustomTaskTypeRequiredFor",
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
                    "custom_task_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="required_for",
                        to="trainings.CustomTaskType",
                    ),
                ),
                (
                    "required_for",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="trainings.Responsibility",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CustomTaskTypeSupersede",
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
                    "custom_task_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="supersedes",
                        to="trainings.CustomTaskType",
                    ),
                ),
                (
                    "supersede",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="trainings.TaskType",
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="customtasktype",
            unique_together=set([("name", "facility")]),
        ),
    ]
