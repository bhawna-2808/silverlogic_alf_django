# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0020_auto_20141023_1924"),
    ]

    operations = [
        migrations.AddField(
            model_name="trainingevent",
            name="location",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
    ]
