# -*- coding: utf-8 -*-


from django.db import migrations
from django.template.defaultfilters import slugify


def add_default_questions_forward(apps, schema_editor):
    FacilityQuestion = apps.get_model("trainings", "FacilityQuestion")
    FacilityQuestionRule = apps.get_model("trainings", "FacilityQuestionRule")
    Position = apps.get_model("trainings", "Position")
    Responsibility = apps.get_model("trainings", "Responsibility")

    try:
        direct_care = Position.objects.get(name="Direct Care")
    except Position.DoesNotExist:
        return

    try:
        first_aid_cpr = Responsibility.objects.get(name="First Aid and CPR")
        alzheimers = Responsibility.objects.get(
            name="Provides Special Care for Persons with Alzheimer's"
        )
    except Responsibility.DoesNotExist:
        return

    try:
        FacilityQuestion.objects.get(slug=slugify("first aid and cpr"))
    except FacilityQuestion.DoesNotExist:
        question = FacilityQuestion.objects.create(
            question="Does your facility require First Aid & CPR for all Direct Care employees?",
            description="First Aid and CPR responsibility will be added to employees with Direct Care position.",
            slug=slugify("first aid and cpr"),
        )
        FacilityQuestionRule.objects.create(
            facility_question=question,
            position=direct_care,
            responsibility=first_aid_cpr,
        )

    try:
        FacilityQuestion.objects.get(slug=slugify("special care for alzheimers"))
    except FacilityQuestion.DoesNotExist:
        question = FacilityQuestion.objects.create(
            question="Does your facility advertise that they provide special care for persons with ALZHEIMER'S DISEASE AND RELATED DISORDERS?",
            description="Alzheimers responsibility will be added to employees with Direct Care position.",
            slug=slugify("special care for alzheimers"),
        )
        FacilityQuestionRule.objects.create(
            facility_question=question, position=direct_care, responsibility=alzheimers
        )

    try:
        FacilityQuestion.objects.get(slug=slugify("secured areas for alzheimers"))
    except FacilityQuestion.DoesNotExist:
        question = FacilityQuestion.objects.create(
            question="Does your facility maintain secured areas ALZHEIMER'S DISEASE AND RELATED DISORDERS?",
            description="Alzheimers responsibility will be added to employees with Direct Care position.",
            slug=slugify("secured areas for alzheimers"),
        )
        FacilityQuestionRule.objects.create(
            facility_question=question, position=direct_care, responsibility=alzheimers
        )


def add_default_questions_backward(apps, schema_editor):
    FacilityQuestion = apps.get_model("trainings", "FacilityQuestion")

    try:
        first_aid_cpr = FacilityQuestion.objects.get(slug=slugify("first aid and cpr"))
        first_aid_cpr.delete()
    except FacilityQuestion.DoesNotExist:
        pass

    try:
        special_care = FacilityQuestion.objects.get(slug=slugify("special care for alzheimers"))
        special_care.delete()
    except FacilityQuestion.DoesNotExist:
        pass

    try:
        secured_area = FacilityQuestion.objects.get(slug=slugify("secured areas for alzheimers"))
        secured_area.delete()
    except FacilityQuestion.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0057_auto_20150706_1430"),
    ]

    operations = [
        migrations.RunPython(add_default_questions_forward, add_default_questions_backward)
    ]
