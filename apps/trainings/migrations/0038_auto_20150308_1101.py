# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0037_employee_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="deactivation_date",
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="employee",
            name="deactivation_note",
            field=models.TextField(default="", blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="employee",
            name="deactivation_reason",
            field=models.PositiveSmallIntegerField(
                default=None, null=True, blank=True, choices=[(1, "Quit"), (2, "Fired")]
            ),
            preserve_default=True,
        ),
    ]
