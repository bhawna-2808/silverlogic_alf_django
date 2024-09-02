# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0045_tasktype_rule"),
    ]

    operations = [
        migrations.AddField(
            model_name="position",
            name="description",
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
