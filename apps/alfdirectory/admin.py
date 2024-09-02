from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import re_path, reverse

from .forms import UploadDirectoryPdfForm
from .models import Facility
from .utils import import_facilities_from_pdf


class FacilityAdmin(admin.ModelAdmin):
    change_list_template = "alfdirectory/admin/change_list.html"
    list_display = (
        "name",
        "state",
        "license_number",
        "oss_beds",
        "private_beds",
        "capacity",
    )
    search_fields = (
        "name",
        "=license_number",
    )
    ordering = ("name",)
    fields = ("name", "license_number", "oss_beds", "private_beds", "state")
    list_filter = ("state",)

    def capacity(self, obj):
        return obj.capacity

    capacity.admin_order_field = "_capacity"

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = super(FacilityAdmin, self).get_urls()
        my_urls = [
            re_path(
                r"^upload-directory-pdf/$",
                self.upload_directory_pdf_view,
                name="%s_%s_upload_directory_pdf" % info,
            ),
        ]
        return my_urls + urls

    def upload_directory_pdf_view(self, request):
        opts = self.model._meta

        if request.method == "POST":
            form = UploadDirectoryPdfForm(request.POST, request.FILES)
            if form.is_valid():
                return self.handle_upload(request)
        else:
            form = UploadDirectoryPdfForm()
        context = {"form": form, "opts": opts}
        return render(request, "alfdirectory/admin/upload_directory_pdf.html", context)

    def handle_upload(self, request):
        temp_file_name = "/tmp/alf-directory-upload.pdf"
        f = request.FILES["pdf_file"]
        with open(temp_file_name, "w") as destination:
            for chunk in f.chunks():
                destination.write(chunk)

        facilities = import_facilities_from_pdf(temp_file_name)

        messages.success(request, "Imported %s facilities" % len(facilities))
        return HttpResponseRedirect(
            reverse(
                "admin:%s_%s_changelist" % (self.model._meta.app_label, self.model._meta.model_name)
            )
        )


admin.site.register(Facility, FacilityAdmin)
