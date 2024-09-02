from datetime import datetime

from django.contrib.staticfiles.storage import staticfiles_storage

from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas


def get_template_pdf():
    f = staticfiles_storage.open("facilities/ba-agreement-template.pdf", "rb")
    content = f.read()
    f.close()
    return content


def generate_pdf(f, facility, user, signature=None):
    template_pdf = get_template_pdf()
    pages = PdfReader(fdata=template_pdf).pages
    document = Canvas(f, pagesize=letter)

    rl_obj = makerl(document, pagexobj(pages[0]))
    document.doForm(rl_obj)
    document.setFontSize(10)
    document.drawString(312, 668, datetime.today().strftime("%-d."))
    document.drawString(360, 668, datetime.today().strftime("%B"))
    document.drawString(450, 668, datetime.today().strftime("%y"))
    document.drawString(51, 655, facility.name)
    document.showPage()

    rl_obj = makerl(document, pagexobj(pages[1]))
    document.doForm(rl_obj)
    document.setFontSize(10)
    document.drawString(285, 247, datetime.today().strftime("%B %-d, %Y"))
    document.showPage()

    rl_obj = makerl(document, pagexobj(pages[2]))
    document.doForm(rl_obj)
    document.setFontSize(10)
    document.drawString(51, 272, "{} {}".format(user.first_name, user.last_name))
    if signature:
        document.drawImage(ImageReader(signature), 51, 237, 120, 20, mask="auto")

    document.drawString(51, 205, datetime.today().strftime("%m/%d/%y"))
    document.drawString(51, 307, facility.name)
    document.drawString(280, 307, "Pascal Bergeron")
    document.drawString(280, 272, "ALF Boss")
    document.drawString(280, 205, datetime.today().strftime("%m/%d/%y"))
    document.showPage()

    document.setTitle("Business Agreement - {}".format(facility.name))
    document.save()

    return f
