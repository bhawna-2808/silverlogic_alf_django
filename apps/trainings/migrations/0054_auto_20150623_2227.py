# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0053_remove_facility_admin_direct_care"),
    ]

    operations = [
        migrations.CreateModel(
            name="FacilityQuestion",
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
                ("question", models.CharField(max_length=512)),
                ("is_license", models.BooleanField(default=False)),
                ("description", models.TextField()),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="FacilityQuestionRule",
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
                (
                    "facility_question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rules",
                        to="trainings.FacilityQuestion",
                    ),
                ),
                (
                    "position",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="trainings.Position",
                    ),
                ),
                (
                    "responsibility",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="trainings.Responsibility",
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name="facilityquestionrule",
            unique_together=set([("facility_question", "position", "responsibility")]),
        ),
        migrations.AddField(
            model_name="facility",
            name="questions",
            field=models.ManyToManyField(to="trainings.FacilityQuestion", blank=True),
            preserve_default=True,
        ),
    ]
