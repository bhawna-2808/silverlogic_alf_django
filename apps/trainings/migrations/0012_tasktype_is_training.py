# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0011_auto_20141009_2242"),
    ]

    operations = [
        migrations.AddField(
            model_name="tasktype",
            name="is_training",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
