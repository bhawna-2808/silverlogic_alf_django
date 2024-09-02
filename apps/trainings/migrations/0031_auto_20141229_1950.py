# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0030_auto_20141226_1122"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tasktype",
            name="prerequisites",
            field=models.ManyToManyField(to="trainings.TaskType", blank=True),
        ),
    ]
