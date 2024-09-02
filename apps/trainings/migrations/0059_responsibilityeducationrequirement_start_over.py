# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0058_auto_20150706_1432"),
    ]

    operations = [
        migrations.AddField(
            model_name="responsibilityeducationrequirement",
            name="start_over",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
