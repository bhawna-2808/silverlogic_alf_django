# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0006_auto_20141007_1256"),
    ]

    operations = [
        migrations.AlterField(
            model_name="employee",
            name="facility",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="trainings.Facility",
                null=True,
            ),
        ),
    ]
