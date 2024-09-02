# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0026_tasktype_prerequisites"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="first_name",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="employee",
            name="last_name",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
    ]
