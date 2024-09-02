# -*- coding: utf-8 -*-


from django.db import migrations


def rename_misspelled_forward(apps, schema_editor):
    TaskType = apps.get_model("trainings", "TaskType")
    try:
        core_training_edu = TaskType.objects.get(name="Core Training Continuing Educatin")
        core_training_edu.name = "Core Training Continuing Education"
        core_training_edu.save()
    except TaskType.DoesNotExist:
        pass


def rename_misspelled_backward(apps, schema_editor):
    TaskType = apps.get_model("trainings", "TaskType")
    try:
        core_training_edu = TaskType.objects.get(name="Core Training Continuing Education")
        core_training_edu.name = "Core Training Continuing Educatin"
        core_training_edu.save()
    except TaskType.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0050_trainingevent_note"),
    ]

    operations = [migrations.RunPython(rename_misspelled_forward, rename_misspelled_backward)]
