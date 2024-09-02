# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0072_auto_20160502_1312"),
    ]

    operations = [
        migrations.AddField(
            model_name="facility",
            name="is_resident_module_enabled",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
