# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0073_facility_is_resident_module_enabled"),
    ]

    operations = [
        migrations.AlterField(
            model_name="facility",
            name="contact_email",
            field=models.EmailField(max_length=254),
        ),
    ]
