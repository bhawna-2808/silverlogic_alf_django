from django.template.response import TemplateResponse
from django.views.generic.base import TemplateResponseMixin, TemplateView

import weasyprint


class PDFTemplateResponse(TemplateResponse):
    def __init__(self, filename=None, fetcher=None, as_attachment=False, *args, **kwargs):
        kwargs["content_type"] = "application/pdf"
        self.fetcher = fetcher
        super(PDFTemplateResponse, self).__init__(*args, **kwargs)

        if as_attachment:
            if filename:
                self["Content-Disposition"] = 'attachment; filename="%s"' % filename
            else:
                self["Content-Disposition"] = "attachment"

    @property
    def rendered_document(self):
        """Returns the rendered pdf"""
        html = super(PDFTemplateResponse, self).rendered_content
        base_url = self._request.build_absolute_uri("/")
        kwargs = {"string": html, "base_url": base_url}

        if self.fetcher:
            kwargs["url_fetcher"] = self.fetcher

        return weasyprint.HTML(**kwargs).render()

    @property
    def rendered_content(self):
        """Returns the rendered pdf"""
        document = self.rendered_document
        return document.copy([document.pages[0]]).write_pdf()


class PDFTemplateResponseMixin(TemplateResponseMixin):
    response_class = PDFTemplateResponse
    filename = None
    fetcher = None

    def get_filename(self):
        """
        Returns the filename of the rendered PDF.
        """
        return self.filename

    def get_response_as_attachment(self):
        """
        Return True and the response_class will cause the browser to download the PDF, rather
        than trying to display it in the browser.
        """
        return False

    def render_to_response(self, *args, **kwargs):
        """
        Returns a response, giving the filename parameter to PDFTemplateResponse.
        """
        kwargs["filename"] = self.get_filename()
        kwargs["as_attachment"] = self.get_response_as_attachment()
        return super(PDFTemplateResponseMixin, self).render_to_response(
            fetcher=self.fetcher, *args, **kwargs
        )


class PDFTemplateView(TemplateView, PDFTemplateResponseMixin):
    pass
