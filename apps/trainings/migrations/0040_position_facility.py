# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0039_remove_position_facility"),
    ]

    operations = [
        migrations.AddField(
            model_name="position",
            name="facility",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                blank=True,
                to="trainings.Facility",
                null=True,
            ),
            preserve_default=True,
        ),
    ]
