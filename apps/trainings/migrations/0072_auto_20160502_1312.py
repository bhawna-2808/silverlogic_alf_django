# -*- coding: utf-8 -*-


from django.db import migrations, models

import localflavor.us.models

from apps.base.models import UsPhoneNumberField


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0071_auto_20160403_1442"),
    ]

    operations = [
        migrations.AddField(
            model_name="facility",
            name="address_city",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="facility",
            name="address_line1",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="facility",
            name="address_line2",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="facility",
            name="address_zipcode",
            field=localflavor.us.models.USZipCodeField(default="", max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="facility",
            name="contact_email",
            field=models.EmailField(default="", max_length=75),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="facility",
            name="contact_phone",
            field=UsPhoneNumberField(default="", max_length=20),
            preserve_default=False,
        ),
    ]
