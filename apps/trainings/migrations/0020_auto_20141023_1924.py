# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0019_auto_20141021_1849"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="task",
            name="scheduled_date",
        ),
        migrations.AddField(
            model_name="trainingevent",
            name="employee_tasks",
            field=models.ManyToManyField(
                related_name="training_events", to="trainings.Task", blank=True
            ),
            preserve_default=True,
        ),
    ]
