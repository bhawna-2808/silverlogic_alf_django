# -*- coding: utf-8 -*-


from django.db import migrations

import localflavor.us.models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0067_auto_20160226_1255"),
    ]

    operations = [
        migrations.AlterField(
            model_name="employee",
            name="ssn",
            field=localflavor.us.models.USSocialSecurityNumberField(max_length=11, blank=True),
        ),
    ]
