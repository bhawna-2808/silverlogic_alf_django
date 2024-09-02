# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="trainingevent",
            name="expiration_time",
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
