# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Employee",
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
                ("name", models.TextField()),
                ("picture", models.ImageField(upload_to="", blank=True)),
                ("date_of_hire", models.DateField()),
                ("ssn", models.TextField()),
                ("phone_number", models.TextField()),
                ("job_description", models.TextField(blank=True)),
                ("application_references", models.SmallIntegerField(default=0)),
                ("handles_medications", models.BooleanField(default=False)),
                ("handles_food", models.BooleanField(default=False)),
                ("application_on_file", models.BooleanField(default=False)),
                ("hha_or_cna", models.BooleanField(default=False)),
                ("daily_living_assistance", models.BooleanField(default=False)),
                ("infection_control", models.BooleanField(default=False)),
                ("level2_background", models.BooleanField(default=False)),
                ("negative_tb", models.BooleanField(default=False)),
                ("freedom_from_comm_disease", models.BooleanField(default=False)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Facility",
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
                ("name", models.TextField()),
                (
                    "admin_direct_care",
                    models.BooleanField(default=False, verbose_name="Admin provides direct care"),
                ),
                (
                    "adrd",
                    models.BooleanField(
                        default=False,
                        verbose_name="Provides special care for persons with ADRD",
                    ),
                ),
                (
                    "first_aid_cpr",
                    models.BooleanField(default=False, verbose_name="Requires First Aid & CPR"),
                ),
            ],
            options={
                "verbose_name_plural": "facilities",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Position",
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
                ("name", models.TextField()),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TrainingEvent",
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
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField()),
                ("attendees", models.ManyToManyField(to="trainings.Employee")),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TrainingType",
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
                ("name", models.TextField()),
                ("validity_period", models.DurationField()),
                ("required_for", models.ManyToManyField(to="trainings.Position")),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name="trainingevent",
            name="type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="trainings.TrainingType"
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="employee",
            name="facility",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="trainings.Facility"
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="employee",
            name="positions",
            field=models.ManyToManyField(to="trainings.Position"),
            preserve_default=True,
        ),
    ]
