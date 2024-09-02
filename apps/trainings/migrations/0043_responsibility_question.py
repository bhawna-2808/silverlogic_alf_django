# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0042_auto_20150323_1806"),
    ]

    operations = [
        migrations.AddField(
            model_name="responsibility",
            name="question",
            field=models.TextField(default="", blank=True),
            preserve_default=True,
        ),
    ]
