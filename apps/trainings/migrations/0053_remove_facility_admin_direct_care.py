# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0052_auto_20150615_1028"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="facility",
            name="admin_direct_care",
        ),
    ]
