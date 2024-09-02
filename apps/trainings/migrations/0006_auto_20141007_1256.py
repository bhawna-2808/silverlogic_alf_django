# -*- coding: utf-8 -*-


import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0005_auto_20141006_1832"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="is_staff",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="employee",
            name="last_login",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="last login"
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="employee",
            name="password",
            field=models.CharField(default="", max_length=128, verbose_name="password"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="employee",
            name="username",
            field=models.TextField(unique=True, null=True),
            preserve_default=True,
        ),
    ]
