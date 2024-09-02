# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0013_employee_expected_date_of_hire"),
    ]

    operations = [
        migrations.AlterField(
            model_name="employee",
            name="date_of_hire",
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="employee",
            name="other_responsibilities",
            field=models.ManyToManyField(to="trainings.Responsibility", blank=True),
        ),
        migrations.AlterField(
            model_name="employee",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                null=True,
                blank=True,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
