# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("residents", "0002_auto_20160428_1246"),
    ]

    operations = [
        migrations.AlterField(
            model_name="resident",
            name="dnr_on_file",
            field=models.BooleanField(
                default=False,
                help_text="Do not resuscitate.",
                verbose_name="DNR on file",
            ),
        ),
    ]
