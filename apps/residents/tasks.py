import csv
import logging
import uuid
from datetime import date, timedelta
from zipfile import ZipFile

from django.core.files import File
from django.core.mail import send_mail
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone

from celery import shared_task
from dateutil.parser import parse as parse_date

from apps.api.views import generate_pdf
from apps.residents.models import Provider, ProviderFile
from apps.trainings.tasks import get_emails

from .emails import email_provider_file
from .models import Resident
from .utils import generate_new_ils_file

logger = logging.getLogger(__name__)

HEADER_ITEMS = [
    "MedicaidID",
    "Last",
    "First",
    "Sex",
    "DOB",
    "EFDate",
    "Term Date",
    "BEDHOLD OUT",
    "BEDHOLD IN",
    "DAYS OUT",
    "TERMREASON",
    "Facility Name",
    "Facility Type",
    "MMA Plan",
    "MMA #",
    "CHA",
    "ACS",
    "OSS",
    "EIN",
    "NPI",
    "PERM. PLACED",
    "Capacity",
    "Available",
]


HEADER_ITEMS_ADMISSION = ["Admitted From"]

HEADER_ITEMS_DISCHARGE = ["Discharged to", "Discharge Reason", "Discharge Notes"]

HEADER_ITEMS_BED_HOLD = ["Bed Hold - Sent to", "Bed Hold Notes"]


@shared_task
def set_resident_is_active():
    Resident.objects.filter(date_of_discharge=timezone.now().date()).update(is_active=False)


@shared_task
def email_resident_birthday_reminder():
    tomorrow = (timezone.now() + timedelta(days=1)).date()
    for resident in Resident.objects.filter(
        is_active=True,
        date_of_birth__month=tomorrow.month,
        date_of_birth__day=tomorrow.day,
    ):
        admin_emails = get_emails(resident.facility, is_admin=True)

        subject = render_to_string(
            "residents/emails/birthday-resident-reminder-subject.txt"
        ).strip()
        message = render_to_string(
            "residents/emails/birthday-resident-reminder-body.txt",
            {
                "full_name": resident.full_name,
            },
        )
        send_mail(subject, message, from_email=None, recipient_list=admin_emails)


@shared_task
def generate_ils_file():
    generate_new_ils_file()
    # TODO: Implement correct PDF generation for providers in stories related to ALF-2190.
    # email_provider_file(ils_file)


@shared_task
def send_ltc_providers_email():
    EmailLTCFiles().send_ltc_providers_email()


@shared_task
def send_ltc_status_notification(resident_id, amends):
    EmailLTCFiles().send_ltc_status_notification(resident_id, amends)


class EmailLTCFiles:
    def __init__(self):
        self.number_of_residents = {}

    def get_date(self, dt):
        if not dt:
            return ""
        if isinstance(dt, str):
            return parse_date(dt).strftime("%m/%d/%Y")
        return dt.strftime("%m/%d/%Y")

    def get_days_out(self, bed_hold):
        if not bed_hold:
            return "0"

        if bed_hold.date_in and bed_hold.date_out:
            return str((bed_hold.date_in - bed_hold.date_out).days)

        if bed_hold.date_out:
            return str((date.today() - bed_hold.date_out).days)

        return "0"

    def get_facility_type(self, facility):
        extended = facility.questions.filter(question="Extended Congregate Care License").exists()
        limited = facility.questions.filter(question="Limited Mental Health License").exists()
        if extended and limited:
            return "ECC, LMH"
        if extended:
            return "ECC"
        if limited:
            return "LMH"
        return "S"

    def get_number_of_residents(self, facility):
        if facility.id not in self.number_of_residents:
            self.number_of_residents[facility.id] = facility.residents.filter(
                is_active=True
            ).count()
        return self.number_of_residents[facility.id]

    def get_line(self, resident, facility, bed_hold, amends=[]):
        line = [
            resident.medicaid_number,
            resident.last_name,
            resident.first_name,
            resident.sex,
            self.get_date(resident.date_of_birth),
            self.get_date(resident.date_of_admission),
            self.get_date(resident.date_of_discharge),
            self.get_date(bed_hold.date_out) if bed_hold else "",
            self.get_date(bed_hold.date_in) if bed_hold else "",
            self.get_days_out(bed_hold),
            resident.discharge_reason,
            facility.name,
            self.get_facility_type(facility),
            resident.mma_plan,
            resident.mma_number,
            "Y" if resident.is_cha else "",
            "Y" if resident.has_assistive_care_services else "",
            "Y" if resident.has_oss else "",
            facility.tax_id,
            facility.npi,
            "Y",
            facility.capacity,
            facility.capacity - self.get_number_of_residents(facility),
        ]
        if "admission" in amends:
            line += [resident.admitted_from]
        if "discharge" in amends:
            line += [
                resident.discharged_to,
                resident.discharge_reason,
                resident.discharge_notes,
            ]
        if "bed_hold" in amends:
            line += [bed_hold.sent_to, bed_hold.notes]
        return line

    def send_to_provider(self, provider, provider_name, residents):
        today = date.today()
        lines = []
        for resident in residents:
            facility = resident.facility
            bed_holds = resident.bed_holds.all() or [None]

            for bed_hold in bed_holds:
                lines.append(self.get_line(resident, facility, bed_hold))

        dt = today.strftime("%Y%m%d")
        csv_name = f"ltc-{provider_name}-{dt}.csv"
        csv_path = f"/tmp/{csv_name}"
        with open(csv_path, "w") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(HEADER_ITEMS)
            csvwriter.writerows(lines)

        pdf_name = f"ltc-{provider_name}-{dt}.pdf"
        pdf_path = f"/tmp/{pdf_name}"
        with open(pdf_path, "wb") as pdffile:
            context = {
                "title": provider_name,
                "header_items": HEADER_ITEMS,
                "lines": lines,
            }
            generate_pdf("residents/ltc-residents.pdf.html", pdffile, context)

        zip_name = f"ltc-{provider_name}-{dt}.zip"
        zip_path = f"/tmp/{zip_name}"
        zip_file = ZipFile(zip_path, "w")
        zip_file.write(csv_path, csv_name)
        zip_file.write(pdf_path, pdf_name)
        zip_file.close()

        with open(zip_name, "rb") as zip_file:
            provider_file = ProviderFile(
                provider=provider,
            )
            provider_file.file = File(zip_file, name=zip_name)
            provider_file.save()
            email_provider_file(provider_file, provider)

    def send_ltc_providers_email(self):
        today = date.today()
        active_residents = Resident.objects.filter(
            Q(date_of_discharge__isnull=True) | Q(date_of_discharge__gte=today),
            date_of_admission__lte=today,
        ).select_related("facility")

        providers = ["fcc", "simply", "sunshine"]
        for provider_name in providers:
            provider_qs = Provider.objects.filter(name__icontains=provider_name)
            residents = active_residents.filter(long_term_care_provider__icontains=provider_name)

            providers_number = provider_qs.count()
            if providers_number != 1:
                logger.exception(
                    f"Expecting 1 provider for {provider_name} but got {providers_number} instead"
                )
                continue

            if len(residents) == 0:
                logger.exception(f"Got 0 actives residents for {provider_name}")
                continue

            try:
                provider = provider_qs.get()
                self.send_to_provider(provider, provider_name, residents)
            except Exception:
                logger.exception(f"Failed to send LTC e-mail for provider {provider_name}")

    def send_ltc_status_notification(self, resident_id, amends):
        resident = Resident.objects.get(id=resident_id)
        provider_name = resident.long_term_care_provider
        provider_qs = Provider.objects.filter(name__icontains=provider_name)

        providers_number = provider_qs.count()
        if providers_number != 1:
            logger.exception(
                f"Expecting 1 provider for {provider_name} but got {providers_number} instead"
            )
            return
        provider = provider_qs.get()

        facility = resident.facility
        bed_holds = resident.bed_holds.all() or [None]

        subject = "New enrollment"
        headers = HEADER_ITEMS
        if "admission" in amends:
            subject = "New admission"
            headers += HEADER_ITEMS_ADMISSION
        if "discharge" in amends:
            subject = "New discharge"
            headers += HEADER_ITEMS_DISCHARGE
        if "bed_hold" in amends:
            subject = "New bed hold"
            headers += HEADER_ITEMS_BED_HOLD
        subject += f" at {facility.name}"

        lines = []
        for bed_hold in bed_holds:
            lines.append(self.get_line(resident, facility, bed_hold, amends))

        pdf_name = f"status-notification-{provider_name}-{str(uuid.uuid4())}.pdf"
        pdf_path = f"/tmp/{pdf_name}"
        with open(pdf_path, "wb") as pdf_file:
            context = {
                "title": provider_name,
                "header_items": HEADER_ITEMS,
                "lines": lines,
            }
            generate_pdf("residents/ltc-residents.pdf.html", pdf_file, context)

        with open(pdf_path, "rb") as pdf_file:
            provider_file = ProviderFile(
                provider=provider,
            )
            provider_file.file = pdf_file
            body = f"{resident.full_name}'s status at {facility.name} has changed. Please open the attachment to view."
            email_provider_file(provider_file, provider, subject, body)
