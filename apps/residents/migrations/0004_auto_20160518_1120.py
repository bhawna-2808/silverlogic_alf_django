# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.db import migrations, models

import apps.base.models
from apps.base.models import UsPhoneNumberField


class Migration(migrations.Migration):

    dependencies = [
        ("residents", "0003_auto_20160428_1650"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResidentMedication",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("medication", models.CharField(max_length=100)),
                ("dosage", models.CharField(max_length=100)),
                ("directions_for_use", models.CharField(max_length=100)),
                ("route", models.CharField(max_length=100)),
                (
                    "resident",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="medications",
                        to="residents.Resident",
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name="resident",
            name="additional_comments_or_observations",
            field=models.TextField(default="", blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="administrator_or_designee_name",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="administrator_or_designee_signature",
            field=models.ImageField(
                null=True,
                upload_to=apps.base.models.random_name_in(
                    "residents/administrator-or-designee-signatures"
                ),
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="ambulation_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="ambulation_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("S*", "Needs Supervision *"),
                    ("A*", "Needs Assistance *"),
                    ("T", "Total Care"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="bathing_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="bathing_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("S*", "Needs Supervision *"),
                    ("A*", "Needs Assistance *"),
                    ("T", "Total Care"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="can_needs_be_met",
            field=models.BooleanField(
                default=False,
                help_text="In your professional opinion, can this individual's needs be met in an assisted living facility, which is not a medical, nursing or psychiatric facility?",
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="can_needs_be_met_comments",
            field=models.TextField(default="", blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="cognitive_or_behavioral_status",
            field=models.TextField(
                default="", verbose_name="Cognitive or behavioral status", blank=True
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="diet_other_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="does_pose_danger",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="dose_pose_danger_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="dressing_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="dressing_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("S*", "Needs Supervision *"),
                    ("A*", "Needs Assistance *"),
                    ("T", "Total Care"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="eating_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="eating_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("S*", "Needs Supervision *"),
                    ("A*", "Needs Assistance *"),
                    ("T", "Total Care"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="examination_date",
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="examiner_address",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="examiner_medical_license_number",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="examiner_name",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="examiner_phone",
            field=UsPhoneNumberField(default="", max_length=20, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="examiner_signature",
            field=models.ImageField(
                null=True,
                upload_to=apps.base.models.random_name_in("residents/examiner-signatures"),
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="examiner_title",
            field=models.CharField(
                default="",
                max_length=255,
                blank=True,
                choices=[("md", "MD"), ("do", "DO"), ("arnp", "ARNP"), ("pa", "PA")],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="gaurdian_or_recipient_name",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="gaurdian_or_recipient_signature",
            field=models.ImageField(
                null=True,
                upload_to=apps.base.models.random_name_in(
                    "residents/gaurdian-or-recipient-signatures"
                ),
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="handling_financial_affairs_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="handling_financial_affairs_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("S*", "Needs Supervision *"),
                    ("A*", "Needs Assistance *"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="handling_personal_affairs_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="handling_personal_affairs_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("S*", "Needs Supervision *"),
                    ("A*", "Needs Assistance *"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="has_communicable_disease",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="has_communicable_disease_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="has_pressure_sores",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="has_pressure_sores_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="height",
            field=models.CharField(default="", max_length=255, verbose_name="Height", blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="is_able_to_administer_without_assistance",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="is_bedridden",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="is_bedridden_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="is_diet_calorie_controlled",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="is_diet_low_fat_or_low_cholesterol",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="is_diet_no_added_salt",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="is_diet_other",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="is_diet_regular",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="is_elopement_risk",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="making_phone_call_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="making_phone_call_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("S*", "Needs Supervision *"),
                    ("A*", "Needs Assistance *"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="nursing_treatment_therapy_service_requirements",
            field=models.TextField(
                default="",
                verbose_name="Nursing/treatment/therapy service requirements",
                blank=True,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="observering_wellbeing_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="observing_wellbeing_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("W", "Weekly"),
                    ("D", "Daily"),
                    ("O*", "Other *"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="observing_whereabouts_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="observing_whereabouts_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("W", "Weekly"),
                    ("D", "Daily"),
                    ("O*", "Other *"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="physical_or_sensory_limitations",
            field=models.TextField(
                default="", verbose_name="Physical or sensory limitations", blank=True
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="preparing_meals_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="preparing_meals_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("S*", "Needs Supervision *"),
                    ("A*", "Needs Assistance *"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="reminders_for_important_tasks_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="reminders_for_important_tasks_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("W", "Weekly"),
                    ("D", "Daily"),
                    ("O*", "Other *"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="requires_help_taking_medication",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="requires_help_with_self_administered_medication",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="requires_medication_administration",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="requires_nursing_or_psychiatric_care",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="requires_nursing_or_psychiatric_care_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="section_2_a_other_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="section_2_a_other_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("S*", "Needs Supervision *"),
                    ("A*", "Needs Assistance *"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="section_2_b_additional_comments",
            field=models.TextField(default="", blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="section_2_b_other1_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="section_2_b_other1_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("W", "Weekly"),
                    ("D", "Daily"),
                    ("O*", "Other *"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="section_2_b_other2_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="section_2_b_other2_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("W", "Weekly"),
                    ("D", "Daily"),
                    ("O*", "Other *"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="section_2_b_other3_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="section_2_b_other3_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("W", "Weekly"),
                    ("D", "Daily"),
                    ("O*", "Other *"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="section_2_b_other4_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="section_2_b_other4_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("W", "Weekly"),
                    ("D", "Daily"),
                    ("O*", "Other *"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="self_care_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="self_care_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("S*", "Needs Supervision *"),
                    ("A*", "Needs Assistance *"),
                    ("T", "Total Care"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="shopping_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="shopping_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("S*", "Needs Supervision *"),
                    ("A*", "Needs Assistance *"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="special_precautions",
            field=models.TextField(default="", verbose_name="Special precautions", blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="toileting_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="toileting_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("S*", "Needs Supervision *"),
                    ("A*", "Needs Assistance *"),
                    ("T", "Total Care"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="transferring_comments",
            field=models.CharField(default="", max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="transferring_status",
            field=models.CharField(
                default="",
                max_length=2,
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("S*", "Needs Supervision *"),
                    ("A*", "Needs Assistance *"),
                    ("T", "Total Care"),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="weight",
            field=models.CharField(default="", max_length=255, verbose_name="Weight", blank=True),
            preserve_default=False,
        ),
    ]
