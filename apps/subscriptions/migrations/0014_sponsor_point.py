# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-07-20 18:55
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0013_merge_20200116_1411"),
    ]

    operations = [
        migrations.AddField(
            model_name="sponsor",
            name="point",
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
    ]
