# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0062_auto_20150731_1643"),
    ]

    operations = [
        migrations.CreateModel(
            name="FacilityDefault",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "employee_responsibility",
                    models.IntegerField(choices=[(1, "True"), (0, "False"), (-1, "Empty")]),
                ),
                (
                    "facility",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="trainings.Facility",
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
