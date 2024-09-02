# -*- coding: utf-8 -*-


from django.db import migrations


def forward(apps, schema_editor):
    Employee = apps.get_model("trainings", "Employee")

    Employee.objects.filter(positions__name="Administrator", receives_emails=False).update(
        receives_emails=True
    )


def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0066_auto_20160209_0607"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
