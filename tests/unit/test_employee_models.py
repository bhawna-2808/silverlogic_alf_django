from datetime import date

from django.core.exceptions import ValidationError

import pytest
from freezegun import freeze_time

from apps.base.models import validate_us_phone_number
from apps.trainings.tasks import deactivate_employees_after_termination_date

import tests.factories as f

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "input_phone,expected",
    [
        ("8006397663", "(800) 639-7663"),
        ("823-456-7890", "(823) 456-7890"),
        ("  823 456 78-90", "(823) 456-7890"),
    ],
)
def test_us_phone_number(input_phone, expected):
    employee = f.EmployeeFactory()
    employee.phone_number = input_phone
    employee.save()
    employee.refresh_from_db()

    assert employee.phone_number == expected


def test_not_valid_us_phone_number():
    with pytest.raises(ValidationError):
        validate_us_phone_number("1234567890")


@freeze_time("2020-01-02")
def test_task_deactivate_employee_after_termination_date():
    employee = f.EmployeeFactory(is_active=True, deactivation_date=date(2020, 1, 2))
    employee_2 = f.EmployeeFactory(is_active=True, deactivation_date=date(2020, 1, 3))

    deactivate_employees_after_termination_date()
    employee.refresh_from_db()
    employee_2.refresh_from_db()
    assert employee.is_active is False
    assert employee_2.is_active is True
