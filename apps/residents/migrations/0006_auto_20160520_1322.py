# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("residents", "0005_serviceoffered"),
    ]

    operations = [
        migrations.AlterField(
            model_name="resident",
            name="contact_1_email",
            field=models.EmailField(max_length=254, blank=True),
        ),
        migrations.AlterField(
            model_name="resident",
            name="contact_2_email",
            field=models.EmailField(max_length=254, blank=True),
        ),
        migrations.AlterField(
            model_name="resident",
            name="primary_doctor_email",
            field=models.EmailField(max_length=254, blank=True),
        ),
        migrations.AlterField(
            model_name="resident",
            name="psychiatric_doctor_email",
            field=models.EmailField(max_length=254, blank=True),
        ),
    ]
