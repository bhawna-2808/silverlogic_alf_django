# -*- coding: utf-8 -*-


from django.db import migrations


def forward(apps, schema_editor):
    Employee = apps.get_model("trainings", "Employee")
    employees = Employee.objects.all()
    for employee in employees:
        if employee.date_of_hire:
            employee.expected_date_of_hire = employee.date_of_hire
            employee.save()


def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0069_auto_20160318_1424"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
        migrations.RemoveField(
            model_name="employee",
            name="date_of_hire",
        ),
    ]
