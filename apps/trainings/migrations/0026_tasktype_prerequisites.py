# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0025_facility_alzheimer"),
    ]

    operations = [
        migrations.AddField(
            model_name="tasktype",
            name="prerequisites",
            field=models.ManyToManyField(to="trainings.TaskType"),
            preserve_default=True,
        ),
    ]
