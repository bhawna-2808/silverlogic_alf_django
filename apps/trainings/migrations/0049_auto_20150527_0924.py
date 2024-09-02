# -*- coding: utf-8 -*-


from django.db import migrations


def admin_receives_emails_true(apps, schema_editor):
    Employee = apps.get_model("trainings", "Employee")

    for e in Employee.objects.all():
        if e.positions.filter(name="Administrator").exists():
            e.receives_emails = True
            e.save()


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0048_employee_receives_emails"),
    ]

    operations = [
        migrations.RunPython(admin_receives_emails_true, lambda apps, schema_editor: True)
    ]
