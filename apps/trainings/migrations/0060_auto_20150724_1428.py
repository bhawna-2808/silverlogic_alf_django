# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0059_responsibilityeducationrequirement_start_over"),
    ]

    operations = [
        migrations.CreateModel(
            name="Antirequisite",
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
                ("valid_after_hire_date", models.DateField()),
                ("due_date", models.DateField(null=True, blank=True)),
                (
                    "antirequisite_of",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="antirequisite_of",
                        to="trainings.TaskType",
                    ),
                ),
                (
                    "task_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="trainings.TaskType",
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name="antirequisite",
            unique_together=set([("task_type", "antirequisite_of")]),
        ),
        migrations.AddField(
            model_name="task",
            name="antirequisite",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                blank=True,
                to="trainings.Antirequisite",
                null=True,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="taskhistory",
            name="antirequisite",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                blank=True,
                to="trainings.Antirequisite",
                null=True,
            ),
            preserve_default=True,
        ),
    ]
