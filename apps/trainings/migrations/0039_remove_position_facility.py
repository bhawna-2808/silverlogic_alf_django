# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0038_auto_20150308_1101"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="position",
            name="facility",
        ),
    ]
