# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0056_auto_20150704_0216"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="facility",
            name="alzheimer",
        ),
        migrations.RemoveField(
            model_name="facility",
            name="first_aid_cpr",
        ),
        migrations.AddField(
            model_name="facilityquestion",
            name="slug",
            field=models.SlugField(unique=True, null=True, blank=True),
            preserve_default=True,
        ),
    ]
