# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-04-04 10:17


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0114_auto_20190403_0937"),
    ]

    operations = [
        migrations.AlterField(
            model_name="employeecourse",
            name="start_date",
            field=models.DateField(null=True),
        ),
    ]
