# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-30 15:41


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("alfdirectory", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="facility",
            options={"verbose_name_plural": "facilities"},
        ),
    ]
