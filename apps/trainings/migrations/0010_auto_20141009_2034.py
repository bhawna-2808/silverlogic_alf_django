# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0009_employee_is_active"),
    ]

    operations = [
        migrations.RenameField(
            model_name="tasktype",
            old_name="required_after",
            new_name="required_within",
        ),
    ]
