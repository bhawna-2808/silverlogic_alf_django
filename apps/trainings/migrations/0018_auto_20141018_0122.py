# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0017_auto_20141017_2146"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="position",
            options={"ordering": ("name",)},
        ),
        migrations.AlterModelOptions(
            name="responsibility",
            options={"ordering": ("name",), "verbose_name_plural": "responsibilities"},
        ),
        migrations.AddField(
            model_name="employee",
            name="address",
            field=models.TextField(default="", blank=True),
            preserve_default=False,
        ),
    ]
