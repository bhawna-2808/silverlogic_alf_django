# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-08-27 17:20


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0124_courseitemlettersizeimage"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="language",
            field=models.SmallIntegerField(choices=[(1, "English"), (2, "Spanish")], default=1),
        ),
    ]
