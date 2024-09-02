from io import BytesIO

from django.core.files import File
from django.core.files.storage import Storage

import factory
import pytest
from mock import patch

from apps.facilities.models import BusinessAgreement
from apps.facilities.utils import Canvas

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestBusinessAgreementCreate(ApiMixin):
    view_name = "business-agreements-list"

    def test_guest_cant_create(self, client):
        r = client.post(self.reverse())
        h.responseUnauthorized(r)

    def test_manager_cant_create(self, manager_client):
        r = manager_client.post(self.reverse())
        h.responseForbidden(r)

    def test_account_admin_can_create(self, account_admin_client, image_base64, pdf_file):
        BusinessAgreement.objects.all().delete()
        data = {"signature": image_base64}
        with patch.object(Canvas, "drawImage"):
            with patch.object(Storage, "path"):
                with patch("apps.facilities.utils.get_template_pdf", lambda: pdf_file):
                    r = account_admin_client.post(self.reverse(), data)
                    h.responseCreated(r)

    def test_cant_create_when_already_existing(self, account_admin_client, image_base64):
        data = {"signature": image_base64}
        r = account_admin_client.post(self.reverse(), data)
        h.responseBadRequest(r)
        assert (
            r.data["non_field_errors"][0]
            == "Your facility has already signed a business agreement."
        )

    def test_signed_by_is_set_to_account_admin(self, account_admin_client, image_base64, pdf_file):
        BusinessAgreement.objects.all().delete()
        data = {"signature": image_base64}
        with patch.object(Canvas, "drawImage"):
            with patch.object(Storage, "path"):
                with patch("apps.facilities.utils.get_template_pdf", lambda: pdf_file):
                    r = account_admin_client.post(self.reverse(), data)
                    h.responseCreated(r)
                    assert (
                        BusinessAgreement.objects.first().signed_by
                        == account_admin_client.user.facility_users
                    )

    def test_facility_is_set_to_account_admin_facility(
        self, account_admin_client, image_base64, pdf_file
    ):
        BusinessAgreement.objects.all().delete()
        data = {"signature": image_base64}
        with patch.object(Canvas, "drawImage"):
            with patch.object(Storage, "path"):
                with patch("apps.facilities.utils.get_template_pdf", lambda: pdf_file):
                    r = account_admin_client.post(self.reverse(), data)
                    h.responseCreated(r)
                    assert (
                        BusinessAgreement.objects.first().facility == account_admin_client.facility
                    )


class TestBusinessAgreementNew(ApiMixin):
    view_name = "business-agreements-new"

    def test_guest_cant_retrieve(self, client):
        r = client.get(self.reverse())
        h.responseUnauthorized(r)

    def test_manager_cant_retrieve(self, manager_client):
        r = manager_client.get(self.reverse())
        h.responseForbidden(r)

    def test_account_admin_can_retrieve_empty(self, account_admin_client, pdf_file):
        BusinessAgreement.objects.all().delete()
        with patch("apps.facilities.utils.get_template_pdf", lambda: pdf_file):
            r = account_admin_client.get(self.reverse())
            assert r.status_code == 200
            assert r.headers["content-type"] == "application/pdf"


class TestBusinessAgreementDownload(ApiMixin):
    view_name = "business-agreements-download"

    def test_guest_cant_retrieve(self, client):
        facility = f.FacilityFactory(name=factory.Faker("name"))
        r = client.get(self.reverse(kwargs={"pk": facility.businessagreement.pk}))
        h.responseUnauthorized(r)

    def test_manager_cant_retrieve(self, manager_client):
        business_agreement = BusinessAgreement.objects.first()
        r = manager_client.get(self.reverse(kwargs={"pk": business_agreement.pk}))
        h.responseForbidden(r)

    def test_account_admin_can_retrieve_own(self, account_admin_client, pdf_file):
        business_agreement = BusinessAgreement.objects.first()
        business_agreement.pdf = File(BytesIO(pdf_file), name="Business Agreement.pdf")
        business_agreement.save()
        r = account_admin_client.get(self.reverse(kwargs={"pk": business_agreement.pk}))
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"

    def test_account_admin_cant_retrieve_other(self, account_admin_client):
        facility = f.FacilityFactory(name=factory.Faker("name"))
        r = account_admin_client.get(self.reverse(kwargs={"pk": facility.businessagreement.pk}))
        h.responseForbidden(r)
