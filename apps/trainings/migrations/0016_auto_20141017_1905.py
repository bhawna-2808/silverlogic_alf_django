# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0015_auto_20141016_2053"),
    ]

    operations = [
        migrations.AlterField(
            model_name="position",
            name="responsibilities",
            field=models.ManyToManyField(to="trainings.Responsibility", blank=True),
        ),
    ]
