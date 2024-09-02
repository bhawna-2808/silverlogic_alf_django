# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0014_auto_20141016_2033"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="completion_date",
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="task",
            name="expiration_date",
            field=models.DateField(null=True, blank=True),
        ),
    ]
