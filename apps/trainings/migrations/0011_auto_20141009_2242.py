# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("trainings", "0010_auto_20141009_2034"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="employee",
            name="is_staff",
        ),
        migrations.RemoveField(
            model_name="employee",
            name="last_login",
        ),
        migrations.RemoveField(
            model_name="employee",
            name="password",
        ),
        migrations.RemoveField(
            model_name="employee",
            name="username",
        ),
        migrations.AddField(
            model_name="employee",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                null=True,
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="employee",
            name="facility",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="trainings.Facility"
            ),
        ),
    ]
