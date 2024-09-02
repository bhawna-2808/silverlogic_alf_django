# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0033_remove_facility_adrd"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResponsibilityEducationRequirement",
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
                ("hours", models.PositiveSmallIntegerField(default=0)),
                ("timeperiod", models.DurationField()),
                (
                    "type",
                    models.PositiveSmallIntegerField(
                        choices=[(1, "Any"), (2, "Admin"), (3, "Alzheimers")]
                    ),
                ),
                (
                    "interval_base",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="trainings.TaskType",
                    ),
                ),
                (
                    "responsibility",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="education_requirements",
                        to="trainings.Responsibility",
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TaskTypeEducationCredit",
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
                ("hours", models.PositiveSmallIntegerField(default=0)),
                (
                    "type",
                    models.PositiveSmallIntegerField(
                        choices=[(1, "Any"), (2, "Admin"), (3, "Alzheimers")]
                    ),
                ),
                (
                    "tasktype",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="education_credits",
                        to="trainings.TaskType",
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name="task",
            name="employee",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="trainings_task_set",
                to="trainings.Employee",
            ),
        ),
        migrations.AlterField(
            model_name="taskhistory",
            name="employee",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="trainings_taskhistory_set",
                to="trainings.Employee",
            ),
        ),
    ]
