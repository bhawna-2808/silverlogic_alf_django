# -*- coding: utf-8 -*-


from django.db import migrations

from localflavor.us.models import USSocialSecurityNumberField

from apps.base.models import UsPhoneNumberField


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0007_auto_20141008_2043"),
    ]

    operations = [
        migrations.AlterField(
            model_name="employee",
            name="phone_number",
            field=UsPhoneNumberField(max_length=20),
        ),
        migrations.AlterField(
            model_name="employee",
            name="ssn",
            field=USSocialSecurityNumberField(max_length=11),
        ),
    ]
