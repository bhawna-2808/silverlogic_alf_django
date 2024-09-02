# -*- coding: utf-8 -*-


from django.db import migrations, models

from apps.base.models import UsPhoneNumberField


class Migration(migrations.Migration):

    dependencies = [
        ("residents", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="resident",
            old_name="notes",
            new_name="personal_notes",
        ),
        migrations.AddField(
            model_name="resident",
            name="allergies",
            field=models.TextField(default="", blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="contact_1_address",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="contact_1_email",
            field=models.EmailField(default="", max_length=75, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="contact_1_name",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="contact_1_phone",
            field=UsPhoneNumberField(default="", max_length=20, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="contact_1_relationship",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="contact_2_address",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="contact_2_email",
            field=models.EmailField(default="", max_length=75, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="contact_2_name",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="contact_2_phone",
            field=UsPhoneNumberField(default="", max_length=20, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="contact_2_relationship",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="contract_amount",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="diagnosis",
            field=models.TextField(default="", blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="dnr_on_file",
            field=models.BooleanField(default=False, help_text="Do not resuscitate."),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="drug_plan_name",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="drug_plan_number",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="financial_notes",
            field=models.TextField(default="", blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="form_1823_completed_date",
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="has_assistive_care_services",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="has_completed_1823_on_file",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="has_durable_power_of_attorney_on_file",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="has_long_term_care_program",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="has_oss",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="has_signed_contract_on_file",
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="resident",
            name="long_term_care_number",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="long_term_care_provider",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="medical_notes",
            field=models.TextField(default="", blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="mma_number",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="mma_plan",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="primary_doctor_address",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="primary_doctor_email",
            field=models.EmailField(default="", max_length=75, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="primary_doctor_name",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="primary_doctor_phone",
            field=UsPhoneNumberField(default="", max_length=20, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="primary_insurance",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="primary_insurance_number",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="psychiatric_doctor_address",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="psychiatric_doctor_email",
            field=models.EmailField(default="", max_length=75, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="psychiatric_doctor_name",
            field=models.CharField(default="", max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="resident",
            name="psychiatric_doctor_phone",
            field=UsPhoneNumberField(default="", max_length=20, blank=True),
            preserve_default=False,
        ),
    ]
