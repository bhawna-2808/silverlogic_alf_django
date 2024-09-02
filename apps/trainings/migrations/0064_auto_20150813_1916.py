# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0063_facilitydefault"),
    ]

    operations = [
        migrations.AlterField(
            model_name="facilitydefault",
            name="employee_responsibility",
            field=models.IntegerField(
                default=-1, choices=[(1, "True"), (0, "False"), (-1, "Empty")]
            ),
        ),
        migrations.AlterField(
            model_name="facilitydefault",
            name="facility",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="default",
                to="trainings.Facility",
            ),
        ),
    ]
