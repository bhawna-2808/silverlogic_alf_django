import re

import requests
from bs4 import BeautifulSoup
from celery import shared_task

from .utils import import_facilities_from_pdf

AHCA_BASE_URL = "http://ahca.myflorida.com/MCHQ/Health_Facility_Regulation/Assisted_Living/"
AHCA_DOWNLOADS_URL = AHCA_BASE_URL + "alf.shtml"
PDF_URL_RE = re.compile("^docs/alf/Directory_ALF")


@shared_task
def import_ahca_facilities():
    r = requests.get(AHCA_DOWNLOADS_URL)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "lxml")
        pdf_url = soup.find(href=PDF_URL_RE)
        if pdf_url:
            full_pdf_url = "{}{}".format(AHCA_BASE_URL, pdf_url.get("href"))
            r = requests.get(full_pdf_url, stream=True)
            if r.status_code == 200:
                temp_file_name = "/tmp/alf-directory-upload.pdf"
                with open(temp_file_name, "w") as destination:
                    for chunk in r.iter_content():
                        destination.write(chunk)

                import_facilities_from_pdf(temp_file_name)
