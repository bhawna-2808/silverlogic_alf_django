# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0041_auto_20150321_1139"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="tasktypeeducationcredit",
            name="hours",
        ),
        migrations.AddField(
            model_name="taskhistory",
            name="credit_hours",
            field=models.FloatField(default=0, blank=True),
            preserve_default=True,
        ),
    ]
