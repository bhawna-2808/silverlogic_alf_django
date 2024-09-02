# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0036_auto_20150219_1911"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="email",
            field=models.EmailField(max_length=254, null=True, blank=True),
            preserve_default=True,
        ),
    ]
