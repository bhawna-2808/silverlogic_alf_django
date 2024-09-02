# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0044_merge"),
    ]

    operations = [
        migrations.AddField(
            model_name="tasktype",
            name="rule",
            field=models.TextField(default="", blank=True),
            preserve_default=True,
        ),
    ]
