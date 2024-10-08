# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-24 20:21


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("residents", "0007_auto_20160524_1612"),
    ]

    operations = [
        migrations.AlterField(
            model_name="resident",
            name="ambulation_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="bathing_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="dose_pose_danger_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="dressing_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="eating_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="handling_financial_affairs_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="handling_personal_affairs_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="has_communicable_disease_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="has_pressure_sores_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="is_bedridden_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="making_phone_call_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="observering_wellbeing_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="observing_whereabouts_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="preparing_meals_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="reminders_for_important_tasks_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="requires_nursing_or_psychiatric_care_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="section_2_a_other_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="section_2_b_other1_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="section_2_b_other1_name",
            field=models.CharField(blank=True, max_length=100, verbose_name="Other name"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="section_2_b_other1_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("W", "Weekly"),
                    ("D", "Daily"),
                    ("O*", "Other *"),
                ],
                max_length=2,
                verbose_name="Status",
            ),
        ),
        migrations.AlterField(
            model_name="resident",
            name="section_2_b_other2_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="section_2_b_other2_name",
            field=models.CharField(blank=True, max_length=100, verbose_name="Other name"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="section_2_b_other2_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("W", "Weekly"),
                    ("D", "Daily"),
                    ("O*", "Other *"),
                ],
                max_length=2,
                verbose_name="Status",
            ),
        ),
        migrations.AlterField(
            model_name="resident",
            name="section_2_b_other3_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="section_2_b_other3_name",
            field=models.CharField(blank=True, max_length=100, verbose_name="Other name"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="section_2_b_other3_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("W", "Weekly"),
                    ("D", "Daily"),
                    ("O*", "Other *"),
                ],
                max_length=2,
                verbose_name="Status",
            ),
        ),
        migrations.AlterField(
            model_name="resident",
            name="section_2_b_other4_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="section_2_b_other4_name",
            field=models.CharField(blank=True, max_length=100, verbose_name="Other name"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="section_2_b_other4_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("I", "Independent"),
                    ("W", "Weekly"),
                    ("D", "Daily"),
                    ("O*", "Other *"),
                ],
                max_length=2,
                verbose_name="Status",
            ),
        ),
        migrations.AlterField(
            model_name="resident",
            name="self_care_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="shopping_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="toileting_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
        migrations.AlterField(
            model_name="resident",
            name="transferring_comments",
            field=models.CharField(blank=True, max_length=100, verbose_name="Comments"),
        ),
    ]
