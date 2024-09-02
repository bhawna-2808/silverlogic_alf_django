# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0031_auto_20141229_1950"),
    ]

    operations = [
        migrations.AddField(
            model_name="tasktype",
            name="is_one_off",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
