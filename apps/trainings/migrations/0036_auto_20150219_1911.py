# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0035_auto_20150215_1314"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tasktype",
            name="facility",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                blank=True,
                to="trainings.Facility",
                null=True,
            ),
        ),
    ]
