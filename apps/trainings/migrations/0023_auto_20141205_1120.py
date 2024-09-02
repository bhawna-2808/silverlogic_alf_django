# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0022_auto_20141130_0041"),
    ]

    operations = [
        migrations.AddField(
            model_name="position",
            name="facility",
            field=models.ManyToManyField(default=None, to="trainings.Facility", blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="responsibility",
            name="facility",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                default=None,
                to="trainings.Facility",
                null=True,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="tasktype",
            name="facility",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                default=None,
                to="trainings.Facility",
                null=True,
            ),
            preserve_default=True,
        ),
    ]
