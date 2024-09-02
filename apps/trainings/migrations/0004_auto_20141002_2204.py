# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0003_auto_20141002_2155"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="tasktype",
            name="required_for",
        ),
        migrations.AddField(
            model_name="tasktype",
            name="required_for",
            field=models.ManyToManyField(to="trainings.Responsibility"),
        ),
    ]
