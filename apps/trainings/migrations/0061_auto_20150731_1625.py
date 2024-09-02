# -*- coding: utf-8 -*-


from django.db import migrations

import autoslug.fields

import apps.trainings.models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0060_auto_20150724_1428"),
    ]

    operations = [
        migrations.AlterField(
            model_name="facilityquestion",
            name="slug",
            field=autoslug.fields.AutoSlugField(
                populate_from=apps.trainings.models.facility_question_slug_populate_from,
                editable=False,
                slugify=apps.trainings.models.facility_question_slug_slugify,
            ),
        ),
    ]
