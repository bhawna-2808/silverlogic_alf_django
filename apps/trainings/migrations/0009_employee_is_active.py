# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0008_auto_20141008_2150"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="is_active",
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
