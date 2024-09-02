# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0016_auto_20141017_1905"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="status",
            field=models.SmallIntegerField(
                choices=[
                    (1, "Open"),
                    (2, "Scheduled"),
                    (3, "Incomplete"),
                    (4, "Completed"),
                ]
            ),
        ),
    ]
