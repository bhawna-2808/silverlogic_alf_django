import operator
import re
import subprocess
from functools import reduce

from django.db import transaction
from django.db.models import Q

from .models import Facility


def import_facilities_from_pdf(temp_file_name):
    name_re = re.compile(r"\s{3,}(.+?)\s{2,}LIC TYPE")
    license_re = re.compile(r"License #(\d+)")
    oss_bed_re = re.compile(r"OSS BEDS : (\d+)")
    private_beds_label = re.compile(r"PRIVATE BEDS[ :]*$")
    private_beds_value = re.compile(r"(\d+)$")

    facilities = []
    private_beds_label_found = False

    output = subprocess.check_output(["pdftotext", "-layout", temp_file_name, "-"])
    lines = output.split("\n")

    for line in lines:
        if "LIC TYPE" in line:
            name_match = name_re.search(line)
            if name_match:
                name = name_match.group(1)

        if "License #" in line:
            license_match = license_re.search(line)
            if license_match:
                license_number = license_match.group(1)

        if "OSS BEDS" in line:
            oss_bed_match = oss_bed_re.search(line)
            if oss_bed_match:
                oss_beds = oss_bed_match.group(1)
            else:
                # Some lines don't have a number after OSS Beds: for some reason.
                oss_beds = 0

        if private_beds_label_found:
            private_beds_label_found = False
            private_beds_value_match = private_beds_value.search(line)
            if private_beds_value_match:
                private_beds = private_beds_value_match.group(1)
                facilities.append(
                    Facility(
                        name=name,
                        license_number=license_number,
                        oss_beds=oss_beds,
                        private_beds=private_beds,
                    )
                )

        if private_beds_label.search(line):
            private_beds_label_found = True

    with transaction.atomic():
        Facility.objects.exclude(
            reduce(
                operator.or_,
                (
                    Q(license_number=facility.license_number, name=facility.name)
                    for facility in facilities
                ),
            )
        ).delete()
        for facility in facilities:
            Facility.objects.update_or_create(
                license_number=facility.license_number,
                name=facility.name,
                defaults={
                    "oss_beds": facility.oss_beds,
                    "private_beds": facility.private_beds,
                },
            )

    return facilities
