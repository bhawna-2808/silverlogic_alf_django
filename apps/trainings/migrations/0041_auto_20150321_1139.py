# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0040_position_facility"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="position",
            unique_together=set([("name", "facility")]),
        ),
        migrations.AlterUniqueTogether(
            name="responsibility",
            unique_together=set([("name", "facility")]),
        ),
        migrations.AlterUniqueTogether(
            name="tasktype",
            unique_together=set([("name", "facility")]),
        ),
    ]
