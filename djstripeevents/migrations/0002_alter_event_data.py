# Generated by Django 3.2.17 on 2023-02-03 16:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("djstripeevents", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="data",
            field=models.JSONField(),
        ),
    ]
