# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-12-16 11:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0152_auto_20200918_2044"),
    ]

    operations = [
        migrations.AddField(
            model_name="employeecourseitem",
            name="is_correct",
            field=models.BooleanField(default=False),
        ),
    ]
