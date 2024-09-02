import json
import os
import tempfile
from io import StringIO

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from django.views.generic import TemplateView

import pikepdf
from django_xhtml2pdf.utils import UnsupportedMediaPathException
from pypdf import PdfFileMerger, PdfFileReader
from rest_framework import generics
from rest_framework.response import Response
from timed_auth_token.authentication import TimedAuthTokenAuthentication
from xhtml2pdf import pisa

from ..base.models import PdfParameters
from .authentication import ApiKeyUrlAuthentication


class PdfView(TemplateView, generics.GenericAPIView):
    authentication_classes = [TimedAuthTokenAuthentication, ApiKeyUrlAuthentication]

    def get(self, request, pk=None, *args, **kwargs):
        response = render_to_pdf_response(
            self.template_name,
            self.get_context_data(),
            pdfname=self.get_filename(),
            open_in="inline",
        )
        return response

    def get_filename(self):
        return self.filename


def merge_pdfs(response, extra_files):
    merger = PdfFileMerger()
    with tempfile.NamedTemporaryFile(suffix=".pdf") as output:
        with tempfile.TemporaryFile() as tf:
            tf.write(response.content)
            tf.seek(0)
            merger.append(tf)

            for f in extra_files:
                try:
                    merger.append(PdfFileReader(f.pdf_file, "rb"))
                except OSError:
                    with tempfile.NamedTemporaryFile(suffix=".pdf") as repaired_pdf:
                        file_to_repair = pikepdf.Pdf.open(f.pdf_file)
                        file_to_repair.save(repaired_pdf.name)
                        f.pdf_file.save("pdf", repaired_pdf)
                        f.save()
                    merger.append(PdfFileReader(f.pdf_file, "rb"))

            merger.write(output.name)
        return output.read()


def render_to_pdf_response(template_name, context=None, pdfname=None, open_in="attachment"):
    file_object = HttpResponse(content_type="application/pdf")
    if not pdfname:
        pdfname = "%s.pdf" % os.path.splitext(os.path.basename(template_name))[0]
    file_object["Content-Disposition"] = '{}; filename="{}"'.format(open_in, pdfname)
    return generate_pdf(template_name, file_object, context)


def generate_pdf(template_name, file_object=None, context=None):
    """
    Uses the xhtml2pdf library to render a PDF to the passed file_object, from the
    given template name.

    This returns the passed-in file object, filled with the actual PDF data.
    In case the passed in file object is none, it will return a StringIO instance.

    """
    if not file_object:
        file_object = StringIO.StringIO()
    if not context:
        context = {}
    tmpl = get_template(template_name)
    generate_pdf_template_object(tmpl, file_object, context)
    return file_object


def generate_pdf_template_object(template_object, file_object, context):
    """
    Inner function to pass template objects directly instead of passing a filename
    """
    html = template_object.render(context)
    pisa.CreatePDF(html.encode("UTF-8"), file_object, encoding="UTF-8", link_callback=link_callback)
    return file_object


def link_callback(uri, rel):
    """
    Callback to allow xhtml2pdf/reportlab to retrieve Images,Stylesheets, etc.
    `uri` is the href attribute from the html link element.
    `rel` gives a relative path, but it's not used here.

    """
    if uri.startswith("http"):
        return uri

    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
    else:
        raise UnsupportedMediaPathException(
            "media urls must start with %s or %s" % (settings.MEDIA_URL, settings.STATIC_URL)
        )
    return path


class PdfParametersView(PdfView):
    parameters = None

    def post(self, request):
        pdfParameters = PdfParameters(parameters=json.dumps(request.data))
        pdfParameters.save()
        return Response({"parameters_id": pdfParameters.id})

    def get_parameters(self):
        if not self.parameters:
            id = self.request.query_params.get("parameters_id", "")
            self.parameters = PdfParameters.objects.get(id=id)
        return json.loads(self.parameters.parameters)

    def get(self, request, pk=None, *args, **kwargs):
        response = super(PdfParametersView, self).get(request, pk, *args, **kwargs)
        return response
