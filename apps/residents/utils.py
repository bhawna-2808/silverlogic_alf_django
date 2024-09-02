import tempfile

from django.conf import settings
from django.core.files.base import ContentFile

import pysftp

from apps.base.models import random_name_in

from .models import IlsFile, Resident


def get_date(d):
    if not d:
        return ""
    return d.strftime("%m.%d.%Y")


def get_line(resident, bedhold):
    if bedhold is None:
        date_out = ""
        date_in = ""
    else:
        date_out = get_date(bedhold.date_out)
        date_in = get_date(bedhold.date_in)

    dob = get_date(resident.date_of_birth)
    date_of_admission = get_date(resident.date_of_admission)
    date_of_discharge = get_date(resident.date_of_discharge)
    npi = resident.facility.npi
    facility_id = str(resident.facility.id)
    permanent_placement = "1" if resident.permanent_placement else "0"

    return "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" % (
        resident.medicaid_number,
        dob,
        date_of_admission,
        date_of_discharge,
        date_in,
        date_out,
        npi,
        facility_id,
        resident.discharge_reason,
        permanent_placement,
    )


def generate_new_ils_file():
    filename = ".txt"
    content = "MedicaidID|DOB|EFDATE|TERMDATE|BEDHOLDDATE_IN|BEDHOLDDATE_OUT|PROVIDERNPI|LOCATIONID|TERMREASON|PERMANENTLYPLACED|\n"

    residents = Resident.objects.filter(
        long_term_care_provider="FCC", medicaid_number__isnull=False
    ).exclude(medicaid_number="")
    for resident in residents:
        bedholds = resident.bed_holds.all()
        if len(bedholds) == 0:
            content += get_line(resident, None)
        for bedhold in bedholds:
            content += get_line(resident, bedhold)

    ils_file = IlsFile()
    ils_file.generated_file.save(filename, ContentFile(content))


def upload_ils_file(filename):
    with pysftp.Connection(
        host=settings.ILS_SFTP_HOST,
        username=settings.ILS_SFTP_USER,
        password=settings.ILS_SFTP_PASS,
    ) as srv:
        with srv.cd(settings.ILS_SFTP_DEST_FOLDER):
            srv.put(filename)


def upload_ils_files():
    for ils_file in IlsFile.objects.filter(uploaded=False):
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(ils_file.generated_file.read())
            upload_ils_file(temp_file.name)


def provider_file_path(instance, filename):
    return random_name_in(f"provider_files/{instance.provider.name}/")(instance, filename)
