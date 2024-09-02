# -*- coding: utf-8 -*-


from django.db import migrations


def forward(apps, schema_editor):
    Employee = apps.get_model("trainings", "Employee")
    employees = Employee.objects.all()
    for employee in employees:
        user = employee.user
        if user and employee.email:
            user.email = employee.email
            user.save()


def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0065_auto_20150820_0417"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
