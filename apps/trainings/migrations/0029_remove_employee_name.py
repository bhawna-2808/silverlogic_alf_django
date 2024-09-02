# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0028_auto_20141222_1152"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="employee",
            name="name",
        ),
    ]
