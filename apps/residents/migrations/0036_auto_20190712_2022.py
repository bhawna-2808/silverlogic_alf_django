# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-07-12 20:22


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("residents", "0035_auto_20190705_1658"),
    ]

    operations = [
        migrations.AlterField(
            model_name="resident",
            name="permanent_placement",
            field=models.BooleanField(default=True),
        ),
    ]
