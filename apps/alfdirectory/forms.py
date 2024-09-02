from django import forms


class UploadDirectoryPdfForm(forms.Form):
    pdf_file = forms.FileField()
