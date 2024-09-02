# -*- coding: utf-8 -*-


import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0004_auto_20141002_2204"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="responsibility",
            options={"verbose_name_plural": "responsibilities"},
        ),
        migrations.AddField(
            model_name="tasktype",
            name="required_after",
            field=models.DurationField(default=datetime.timedelta(0)),
            preserve_default=False,
        ),
    ]
