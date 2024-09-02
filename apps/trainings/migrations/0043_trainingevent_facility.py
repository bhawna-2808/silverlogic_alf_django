# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0042_auto_20150323_1806"),
    ]

    operations = [
        migrations.AddField(
            model_name="trainingevent",
            name="facility",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                default=1,
                to="trainings.Facility",
            ),
            preserve_default=False,
        ),
    ]
