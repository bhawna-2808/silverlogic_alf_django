# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0150_auto_20200720_2123"),
    ]

    operations = [
        migrations.AddField(
            model_name="facility",
            name="tax_id",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
