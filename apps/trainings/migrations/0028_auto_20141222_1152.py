# -*- coding: utf-8 -*-


from django.db import migrations


def split_names(apps, schema_editor):
    Employee = apps.get_model("trainings", "Employee")
    for employee in Employee.objects.all():
        names = employee.name.split(" ", 1)

        employee.first_name = names[0]

        # The employee might not have a last name entered
        if len(names) > 1:
            employee.last_name = names[1]
        else:
            employee.last_name = ""
        employee.save()


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0027_auto_20141222_1145"),
    ]

    operations = [migrations.RunPython(split_names)]
