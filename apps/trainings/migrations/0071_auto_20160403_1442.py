# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0070_remove_employee_date_of_hire"),
    ]

    operations = [
        migrations.RenameField(
            model_name="employee",
            old_name="expected_date_of_hire",
            new_name="date_of_hire",
        ),
    ]
