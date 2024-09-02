from copy import deepcopy

from django.contrib.auth.models import User

import pytest

from apps.activities.models import Activity
from apps.facilities.models import FacilityUser
from apps.trainings.models import Employee, Facility

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestRegister(ApiMixin):
    view_name = "register-list"

    @pytest.fixture
    def data(self):
        f.PositionFactory(name="Administrator")
        self.directory_facility = f.DirectoryFacilityFactory()
        return {
            "facility": {
                "name": "Test Facility",
                "license_number": "1234",
                "address_line1": "123 Fake street",
                "address_city": "San Francisco",
                "state": "CA",
                "address_zipcode": "90210",
                "contact_phone": "5107488230",
                "contact_email": "john@test.com",
            },
            "user": {
                "username": "testuser",
                "password": "1234",
                "conf_password": "1234",
                "first_name": "John",
                "last_name": "Smith",
                "email": "john@smith.com",
            },
            "employee": {
                "date_of_hire": "2021-01-01",
            },
            "terms": {"agree": True},
        }

    def test_can_register(self, client, data):
        r = client.post(self.reverse(), data)
        h.responseCreated(r)

    def test_facility_creation_is_tracked(self, client, data):
        r = client.post(self.reverse(), data)
        h.responseCreated(r)
        assert Activity.objects.count() == 1
        activity = Activity.objects.get()
        user = User.objects.get(username="testuser")
        facility = Facility.objects.get(name="Test Facility")
        assert activity.actor == user
        assert activity.verb == "created facility"
        assert activity.action_object == facility

    def test_both_passwords_must_match(self, client, data):
        data["user"]["conf_password"] = "does not match"
        r = client.post(self.reverse(), data)
        h.responseBadRequest(r)

    def test_new_user_belongs_to_the_new_facility(self, client, data):
        client.post(self.reverse(), data)
        assert FacilityUser.objects.count()

    def test_new_user_has_the_password_hashed(self, client, data):
        client.post(self.reverse(), data)
        user = User.objects.get()
        assert user.check_password(data["user"]["password"])

    def test_new_user_has_their_email_set(self, client, data):
        client.post(self.reverse(), data)
        user = User.objects.get()
        assert user.email == data["user"]["email"]

    def test_new_user_has_their_name_set(self, client, data):
        client.post(self.reverse(), data)
        user = User.objects.get()
        assert user.first_name == data["user"]["first_name"]
        assert user.last_name == data["user"]["last_name"]

    def test_all_fields_are_required(self, client, data):
        orig_data = deepcopy(data)

        for key, value in orig_data.items():
            for sub_key in value:
                data = deepcopy(orig_data)
                data[key].pop(sub_key)
                r = client.post(self.reverse(), data)
                h.responseBadRequest(r)

    def test_sends_welcome_email(self, client, data, outbox):
        r = client.post(self.reverse(), data)
        h.responseCreated(r)

        assert len(outbox) == 1
        message = outbox[0]
        assert message.subject == "Welcome to ALFBoss!"
        assert "username: testuser" in message.body

    def test_facility_can_have_questions_on_create(self, client, data):
        question = f.FacilityQuestionFactory()
        data["facility"]["questions"] = [question.pk]
        client.post(self.reverse(), data)
        assert question.facility_set.count() == 1

    def test_no_facility_is_made_on_errors(self, client, data):
        data["terms"]["agree"] = False  # Will trigger an error
        client.post(self.reverse(), data)
        assert Facility.objects.count() == 0

    def test_primary_administrator_name_is_filled_from_users_name(self, client, data):
        client.post(self.reverse(), data)
        facility = Facility.objects.get()
        assert facility.primary_administrator_name == "John Smith"

    def test_autofills_capacity_from_directory_faciliy(self, client, data):
        r = client.post(self.reverse(), data)
        h.responseCreated(r)
        assert Facility.objects.get().capacity == self.directory_facility.capacity

    def test_license_number_must_be_valid(self, client, data):
        data["facility"]["license_number"] = "9981"
        r = client.post(self.reverse(), data)
        h.responseBadRequest(r)

    def test_license_number_must_be_unique(self, client, data):
        f.DirectoryFacilityFactory(license_number="123")
        f.DirectoryFacilityFactory(license_number="123")
        data["facility"]["license_number"] = "123"
        r = client.post(self.reverse(), data)
        h.responseBadRequest(r)
        assert (
            r.data["facility"]["directory_facility"]["message"][0]
            == "2 facilities with license number 123, please select yours"
        )
        assert len(r.data["facility"]["directory_facility"]["facilities"]) == 2

    def test_license_number_or_facility_id_is_required(self, client, data):
        del data["facility"]["license_number"]
        r = client.post(self.reverse(), data)
        h.responseBadRequest(r)
        assert (
            r.data["facility"]["license_number"][0]
            == "Either license_number or directory_facility is required."
        )

    def test_license_number_or_facility_id_is_required_both_submitted(self, client, data):
        directory_facility = f.DirectoryFacilityFactory()
        data["facility"]["directory_facility"] = directory_facility.pk
        r = client.post(self.reverse(), data)
        h.responseBadRequest(r)
        assert (
            r.data["facility"]["license_number"][0]
            == "Either license_number or directory_facility is required."
        )

    def test_can_set_directory_facility_by_id(self, client, data):
        del data["facility"]["license_number"]
        directory_facility = f.DirectoryFacilityFactory()
        data["facility"]["directory_facility"] = directory_facility.pk
        r = client.post(self.reverse(), data)
        h.responseCreated(r)
        facility = Facility.objects.get()
        assert facility.directory_facility == directory_facility

    def test_is_staff_module_depends_on_fcc_signup(self, client, data):
        data["facility"]["fcc_signup"] = True
        r = client.post(self.reverse(), data)
        h.responseCreated(r)
        facility = Facility.objects.get()
        assert facility.is_staff_module_enabled is False
        facility.delete()

        data["user"]["username"] = "anothertest"
        data["facility"]["fcc_signup"] = False
        r = client.post(self.reverse(), data)
        h.responseCreated(r)
        facility = Facility.objects.get()
        assert facility.is_staff_module_enabled is True

    def test_autocreate_employee(self, client, data):
        r = client.post(self.reverse(), data)
        h.responseCreated(r)

        employee = Employee.objects.get()
        user = User.objects.get()
        assert employee.first_name == user.first_name


class TestEmployeeRegister(ApiMixin):
    view_name = "register-employee"

    @pytest.fixture
    def data(self):
        f.EmployeeFactory(phone_number="(800) 456-7890")
        return {
            "username": "notMyQuixote",
            "password": "sancholove",
            "conf_password": "sancholove",
            "phone": "(800) 456-7890",
        }

    def test_can_register(self, client, data):
        r = client.post(self.reverse(), data)
        h.responseOk(r)

    def test_can_use_wrong_phone_format(self, client, data):
        data["phone"] = "8004567890"
        r = client.post(self.reverse(), data)
        h.responseOk(r)

    def test_cant_use_extra_digits_in_phone(self, client, data):
        data["phone"] = "1234567890123"
        r = client.post(self.reverse(), data)
        h.responseBadRequest(r)
        assert r.data["phone"][0] == "The phone number must have 10 digits"
