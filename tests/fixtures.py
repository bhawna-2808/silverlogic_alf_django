from datetime import date, timedelta
from io import BytesIO

from django.core import mail
from django.core.files.images import ImageFile
from django.utils import timezone

import pytest
from reportlab.pdfgen import canvas
from rest_framework.test import APIClient

from apps.facilities.models import FacilityUser
from apps.subscriptions.models import Plan, Subscription

import tests.factories as f


class Client(APIClient):
    def force_authenticate(self, user):
        self.user = user
        super(Client, self).force_authenticate(user)


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def outbox():
    return mail.outbox


@pytest.fixture
def image_base64():
    return "iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAMAAAAM7l6QAAAARVBMVEXPACr///8HAAIVAARnND5oABVzABcnCA6mACJHAA62ACXhztGcbXfi0dVzP0qZAB86EhqLWWPNsLZUABEjAAcaBAhbKjRAQ1vHAAAA+0lEQVQokYWTCZKEIAxFw2cTV9z6/kftsMjoiG2qVPQlAZMfEod1vfI7sHvVd+Uj5ecyWhSz43LFM0Pp9NS2k3aSHeYTHhSw6YayNZod1HDg4QO4AqPDCnyGjDnW0D/jBCrhuUKZA3PAi8V6p0Qr7MJ4hGxquNkwCuosdI2G9Laj/iGYwyV6UnC8FFeSXh0U+Zi7ig087Zgoli7eiY4m8GqCJKDN7ukSf9EtcMZHjjOOyUt03jktQ3KfKpr3FuUA+Wjpx6oWfuylLC9F5ZZsP1ry1tAHOZgshyAmeeOmiClKcX2W4l3I21nIZQxMGANzG4PXIcojyHHyMoJf+KcJUmsQs8MAAAAASUVORK5CYII="


@pytest.fixture
def image_django_file(image_base64):
    i = BytesIO(image_base64.encode("utf-8"))
    return ImageFile(i, name="image.png")


@pytest.fixture
def pdf_file():
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    for i in range(3):
        p.drawString(100, 100, "Hello world.")
        p.showPage()

    p.save()
    return buffer.getvalue()


@pytest.fixture
def account_admin_client():
    client = Client()
    facility_user = f.FacilityUserFactory(role=FacilityUser.Role.account_admin)
    client.force_authenticate(facility_user.user)
    client.facility = facility_user.facility
    return client


@pytest.fixture
def manager_client():
    client = Client()
    facility_user = f.FacilityUserFactory(role=FacilityUser.Role.manager)
    client.force_authenticate(facility_user.user)
    client.facility = facility_user.facility
    return client


@pytest.fixture
def cloudcare_client():
    client = Client()
    cloudcare_user = f.UserFactory()
    client.force_authenticate(cloudcare_user)
    return client


@pytest.fixture
def employee_client():
    client = Client()
    facility_user = f.FacilityUserFactory(role=FacilityUser.Role.trainings_user)
    f.EmployeeFactory(user=facility_user.user)
    client.force_authenticate(facility_user.user)
    client.facility = facility_user.facility
    return client


@pytest.fixture
def examiner_client():
    client = Client()
    facility_user = f.FacilityUserFactory(role=FacilityUser.Role.examiner)
    examiner = f.ExaminerFactory(user=facility_user.user)
    client.force_authenticate(facility_user.user)
    client.facility = facility_user.facility
    client.examiner = examiner
    return client


@pytest.fixture
def trainings_user_client():
    client = Client()
    facility_user = f.FacilityUserFactory(role=FacilityUser.Role.trainings_user)
    client.force_authenticate(facility_user.user)
    client.facility = facility_user.facility
    return client


@pytest.fixture
def subscription():
    f.SubscriptionFactory()


@pytest.fixture
def resident_subscription():
    return f.SubscriptionFactory(billing_interval__plan__module=Plan.Module.resident)


@pytest.fixture
def resident_and_staff_subscription(resident_subscription):
    f.SubscriptionFactory(
        facility=resident_subscription.facility,
        status=Subscription.Status.trialing,
        billing_interval__plan__module=Plan.Module.staff,
        trial_end=timezone.now() - timedelta(days=1),
    )


@pytest.fixture
def expected_ils_file():
    # Resident with 2 lines (2 BedHolds)
    resident = f.ResidentFactory(
        medicaid_number=2305294933,
        date_of_birth=date(1912, 10, 6),
        date_of_admission=date(2019, 2, 16),
        long_term_care_provider="FCC",
        discharge_reason="Transfer to a New Provider",
        date_of_discharge=date(2019, 5, 17),
        facility=f.FacilityFactory(name="f1", npi="5636462044"),
        permanent_placement=False,
    )
    f.ResidentBedHoldFactory(
        resident=resident, date_out=date(2018, 6, 13), date_in=date(2019, 4, 25)
    )
    f.ResidentBedHoldFactory(
        resident=resident, date_out=date(2019, 1, 6), date_in=date(2019, 3, 13)
    )

    # Another resident
    resident2 = f.ResidentFactory(
        medicaid_number=4022171741,
        date_of_birth=date(1941, 6, 6),
        date_of_admission=date(2018, 11, 9),
        long_term_care_provider="FCC",
        discharge_reason="Deceased",
        facility=f.FacilityFactory(name="f2", npi="5676668978"),
        permanent_placement=True,
    )

    # long_term_care_provider is not "FCC". Should not be added
    f.ResidentFactory()

    return """MedicaidID|DOB|EFDATE|TERMDATE|BEDHOLDDATE_IN|BEDHOLDDATE_OUT|PROVIDERNPI|LOCATIONID|TERMREASON|PERMANENTLYPLACED|
2305294933|10.06.1912|02.16.2019|05.17.2019|04.25.2019|06.13.2018|5636462044|%s|Transfer to a New Provider|0
2305294933|10.06.1912|02.16.2019|05.17.2019|03.13.2019|01.06.2019|5636462044|%s|Transfer to a New Provider|0
4022171741|06.06.1941|11.09.2018||||5676668978|%s|Deceased|1
""" % (
        resident.facility.id,
        resident.facility.id,
        resident2.facility.id,
    )
