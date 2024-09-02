# -*- coding: utf-8 -*-


from django.db import migrations

from apps.base.models import UsPhoneNumberField


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0068_auto_20160301_1004"),
    ]

    operations = [
        migrations.AlterField(
            model_name="employee",
            name="phone_number",
            field=UsPhoneNumberField(max_length=20, blank=True),
        ),
    ]
