# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0024_facility_subdomain"),
    ]

    operations = [
        migrations.AddField(
            model_name="facility",
            name="alzheimer",
            field=models.BooleanField(
                default=False,
                verbose_name=b"Provides special care for persons with Alzheimer's",
            ),
            preserve_default=True,
        ),
    ]
