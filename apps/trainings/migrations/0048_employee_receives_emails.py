# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0047_facility_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="receives_emails",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
