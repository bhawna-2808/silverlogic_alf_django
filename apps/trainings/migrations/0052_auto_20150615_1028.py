# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0051_auto_20150612_0848"),
    ]

    operations = [
        migrations.AlterField(
            model_name="responsibility",
            name="facility",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                default=None,
                blank=True,
                to="trainings.Facility",
                null=True,
            ),
        ),
    ]
