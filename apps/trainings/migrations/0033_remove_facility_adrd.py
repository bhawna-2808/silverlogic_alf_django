# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0032_tasktype_is_one_off"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="facility",
            name="adrd",
        ),
    ]
