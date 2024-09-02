# -*- coding: utf-8 -*-


from django.db import migrations
from django.template.defaultfilters import slugify

import autoslug.fields

import apps.trainings.models


def set_value_for_blank_slugs(apps, schema_editor):
    """
        Sets a value for facility questions with no slugs to avoid the
    following error:

    "django.db.utils.IntegrityError: column "slug" contains null values"
    """
    FacilityQuestion = apps.get_model("trainings", "FacilityQuestion")
    facility_questions = FacilityQuestion.objects.all()
    for facility_question in facility_questions:
        if not facility_question.slug:
            facility_question.slug = slugify(facility_question.question)
            facility_question.save()


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0061_auto_20150731_1625"),
    ]

    operations = [
        migrations.RunPython(set_value_for_blank_slugs, lambda x, y: None),
        migrations.AlterField(
            model_name="facilityquestion",
            name="slug",
            field=autoslug.fields.AutoSlugField(
                populate_from=apps.trainings.models.facility_question_slug_populate_from,
                editable=True,
                unique=True,
                slugify=apps.trainings.models.facility_question_slug_slugify,
            ),
        ),
    ]
