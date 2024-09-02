# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0002_trainingevent_expiration_time"),
    ]

    operations = [
        migrations.CreateModel(
            name="Responsibility",
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
                ("name", models.TextField()),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Task",
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
                ("due_date", models.DateField(null=True)),
                ("completion_date", models.DateField(null=True)),
                ("expiration_date", models.DateField(null=True)),
                (
                    "status",
                    models.SmallIntegerField(
                        choices=[
                            (1, "open"),
                            (2, "scheduled"),
                            (3, "incomplete"),
                            (4, "completed"),
                        ]
                    ),
                ),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="trainings.Employee",
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.RenameModel(
            old_name="TrainingType",
            new_name="TaskType",
        ),
        migrations.AddField(
            model_name="task",
            name="type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="trainings.TaskType"
            ),
            preserve_default=True,
        ),
        migrations.RenameField(
            model_name="trainingevent",
            old_name="type",
            new_name="training_for",
        ),
        migrations.RemoveField(
            model_name="employee",
            name="application_on_file",
        ),
        migrations.RemoveField(
            model_name="employee",
            name="daily_living_assistance",
        ),
        migrations.RemoveField(
            model_name="employee",
            name="freedom_from_comm_disease",
        ),
        migrations.RemoveField(
            model_name="employee",
            name="handles_food",
        ),
        migrations.RemoveField(
            model_name="employee",
            name="handles_medications",
        ),
        migrations.RemoveField(
            model_name="employee",
            name="hha_or_cna",
        ),
        migrations.RemoveField(
            model_name="employee",
            name="infection_control",
        ),
        migrations.RemoveField(
            model_name="employee",
            name="level2_background",
        ),
        migrations.RemoveField(
            model_name="employee",
            name="negative_tb",
        ),
        migrations.RemoveField(
            model_name="trainingevent",
            name="expiration_time",
        ),
        migrations.AddField(
            model_name="employee",
            name="other_responsibilities",
            field=models.ManyToManyField(to="trainings.Responsibility"),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="position",
            name="responsibilities",
            field=models.ManyToManyField(to="trainings.Responsibility"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="employee",
            name="date_of_hire",
            field=models.DateField(null=True),
        ),
    ]
