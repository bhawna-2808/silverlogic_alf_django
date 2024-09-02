# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0029_remove_employee_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="TaskHistory",
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
                ("completion_date", models.DateField(null=True)),
                ("expiration_date", models.DateField(null=True)),
                (
                    "status",
                    models.SmallIntegerField(choices=[(1, "Incomplete"), (2, "Completed")]),
                ),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="trainings.Employee",
                    ),
                ),
                (
                    "type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="trainings.TaskType",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name="task",
            name="completion_date",
        ),
        migrations.RemoveField(
            model_name="task",
            name="expiration_date",
        ),
        migrations.AlterField(
            model_name="task",
            name="status",
            field=models.SmallIntegerField(default=1, choices=[(1, "Open"), (2, "Scheduled")]),
        ),
        migrations.AlterUniqueTogether(
            name="task",
            unique_together=set([("employee", "type")]),
        ),
    ]
