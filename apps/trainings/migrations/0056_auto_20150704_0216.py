# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import DatabaseError, migrations, models


def add_groups(apps, schema_editor):
    PositionGroup = apps.get_model("trainings", "PositionGroup")

    try:
        PositionGroup.objects.create(name="Administrative")
        PositionGroup.objects.create(name="Care")
        PositionGroup.objects.create(name="Food Handling")
        PositionGroup.objects.create(name="Maintenance")
    except DatabaseError:
        pass


def remove_groups(apps, schema_editor):
    # Remove groups manually via admin
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0055_tasktypeeducationcredit_facility"),
    ]

    operations = [
        migrations.CreateModel(
            name="PositionGroup",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("name", models.CharField(unique=True, max_length=128)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.RunPython(add_groups, remove_groups),
        migrations.AddField(
            model_name="position",
            name="group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                blank=True,
                to="trainings.PositionGroup",
                null=True,
            ),
            preserve_default=True,
        ),
    ]
