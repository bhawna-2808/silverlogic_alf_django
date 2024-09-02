# -*- coding: utf-8 -*-


from django.db import migrations, models

import localflavor.us.models

import apps.utils.model_fields


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0034_auto_20150204_1553"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="address2",
            field=models.TextField(default="", blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="employee",
            name="city",
            field=models.TextField(default="", blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="employee",
            name="date_of_birth",
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="employee",
            name="state",
            field=localflavor.us.models.USStateField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("AL", "Alabama"),
                    ("AK", "Alaska"),
                    ("AS", "American Samoa"),
                    ("AZ", "Arizona"),
                    ("AR", "Arkansas"),
                    ("AA", "Armed Forces Americas"),
                    ("AE", "Armed Forces Europe"),
                    ("AP", "Armed Forces Pacific"),
                    ("CA", "California"),
                    ("CO", "Colorado"),
                    ("CT", "Connecticut"),
                    ("DE", "Delaware"),
                    ("DC", "District of Columbia"),
                    ("FL", "Florida"),
                    ("GA", "Georgia"),
                    ("GU", "Guam"),
                    ("HI", "Hawaii"),
                    ("ID", "Idaho"),
                    ("IL", "Illinois"),
                    ("IN", "Indiana"),
                    ("IA", "Iowa"),
                    ("KS", "Kansas"),
                    ("KY", "Kentucky"),
                    ("LA", "Louisiana"),
                    ("ME", "Maine"),
                    ("MD", "Maryland"),
                    ("MA", "Massachusetts"),
                    ("MI", "Michigan"),
                    ("MN", "Minnesota"),
                    ("MS", "Mississippi"),
                    ("MO", "Missouri"),
                    ("MT", "Montana"),
                    ("NE", "Nebraska"),
                    ("NV", "Nevada"),
                    ("NH", "New Hampshire"),
                    ("NJ", "New Jersey"),
                    ("NM", "New Mexico"),
                    ("NY", "New York"),
                    ("NC", "North Carolina"),
                    ("ND", "North Dakota"),
                    ("MP", "Northern Mariana Islands"),
                    ("OH", "Ohio"),
                    ("OK", "Oklahoma"),
                    ("OR", "Oregon"),
                    ("PA", "Pennsylvania"),
                    ("PR", "Puerto Rico"),
                    ("RI", "Rhode Island"),
                    ("SC", "South Carolina"),
                    ("SD", "South Dakota"),
                    ("TN", "Tennessee"),
                    ("TX", "Texas"),
                    ("UT", "Utah"),
                    ("VT", "Vermont"),
                    ("VI", "Virgin Islands"),
                    ("VA", "Virginia"),
                    ("WA", "Washington"),
                    ("WV", "West Virginia"),
                    ("WI", "Wisconsin"),
                    ("WY", "Wyoming"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="employee",
            name="zip_field",
            field=models.CharField(default="", max_length=50, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="tasktype",
            name="supersedes",
            field=models.ManyToManyField(
                related_name="superseded_by", to="trainings.TaskType", blank=True
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="employee",
            name="first_name",
            field=apps.utils.model_fields.ProperNameField(),
        ),
        migrations.AlterField(
            model_name="employee",
            name="last_name",
            field=apps.utils.model_fields.ProperNameField(),
        ),
    ]
