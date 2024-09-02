# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0054_auto_20150623_2227"),
    ]

    operations = [
        migrations.AddField(
            model_name="tasktypeeducationcredit",
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
