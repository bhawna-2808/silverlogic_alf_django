# -*- coding: utf-8 -*-


import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0012_tasktype_is_training"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="expected_date_of_hire",
            field=models.DateField(default=datetime.date(2014, 10, 31)),
            preserve_default=False,
        ),
    ]
