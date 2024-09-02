import pytest
from mock import patch

from apps.trainings.models import Task, TaskType
from apps.trainings.tasks import apply_global_requirement

import tests.factories as f

pytestmark = pytest.mark.django_db


@patch.object(TaskType, "check_capacity")
def test_apply_global_requirement(check_capacity_mock):
    global_requirement = f.GlobalRequirementFactory()
    employee = f.EmployeeFactory()

    # cleaning all the tasks created before
    Task.objects.all().delete()

    apply_global_requirement(global_requirement.pk)
    check_capacity_mock.assert_called_with(employee)
    assert Task.objects.all().count() == 1
