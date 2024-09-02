# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0023_auto_20141205_1120"),
    ]

    operations = [
        migrations.AddField(
            model_name="facility",
            name="subdomain",
            field=models.CharField(max_length=64, null=True, blank=True),
            preserve_default=True,
        ),
    ]
