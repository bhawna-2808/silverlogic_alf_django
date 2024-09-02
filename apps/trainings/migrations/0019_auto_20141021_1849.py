# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0018_auto_20141018_0122"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="scheduled_date",
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="trainingevent",
            name="completed",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
