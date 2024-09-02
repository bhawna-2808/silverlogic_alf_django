# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0049_auto_20150527_0924"),
    ]

    operations = [
        migrations.AddField(
            model_name="trainingevent",
            name="note",
            field=models.TextField(default="", blank=True),
            preserve_default=True,
        ),
    ]
