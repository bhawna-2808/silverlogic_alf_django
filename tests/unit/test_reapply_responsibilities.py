import pytest

from apps.trainings.tasks import reapply_employee_responsibilities

import tests.factories as f

pytestmark = pytest.mark.django_db


def test_reapply_responsibility():
    employee = f.EmployeeFactory()
    employee.other_responsibilities.add(f.ResponsibilityFactory())

    reapply_employee_responsibilities()

    assert employee.other_responsibilities.count() == 1


def test_reapply_add_responsibility_if_position_has_responsibility():
    position = f.PositionFactory()
    position.responsibilities.add(f.ResponsibilityFactory())

    employee = f.EmployeeFactory()
    employee.other_responsibilities.add(f.ResponsibilityFactory())
    employee.positions.add(position)

    employee.other_responsibilities.all().count() == 1
    reapply_employee_responsibilities()
    employee.other_responsibilities.all().count() == 2


@pytest.mark.parametrize("has_question", [True, False])
def test_reapply_add_responsibility_if_facility_has_question(has_question):
    responsibility_1 = f.ResponsibilityFactory()
    responsibility_2 = f.ResponsibilityFactory()

    position = f.PositionFactory()

    employee = f.EmployeeFactory()
    employee.other_responsibilities.add(responsibility_1)
    employee.positions.add(position)

    question = f.FacilityQuestionFactory()
    f.FacilityQuestionRuleFactory(
        facility_question=question, position=position, responsibility=responsibility_2
    )

    if has_question:
        employee.facility.questions.add(question)

    reapply_employee_responsibilities()

    responsibilities = employee.other_responsibilities.all()
    assert responsibility_1 in responsibilities

    if has_question:
        assert employee.other_responsibilities.count() == 2
        assert responsibility_2 in responsibilities
    else:
        assert employee.other_responsibilities.count() == 1
