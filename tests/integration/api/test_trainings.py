import mimetypes
import tempfile
from datetime import date, timedelta

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

import pytest
from mock import patch
from rest_framework import status
from rest_framework.test import APITestCase

from apps.activities.models import Activity
from apps.api.permissions import FacilityHasStaffSubscriptionIfRequired
from apps.api.trainings.serializers import EmployeeReadSerializer
from apps.facilities.models import FacilityUser
from apps.subscriptions.models import Plan, Subscription
from apps.trainings.models import (
    CustomTaskType,
    CustomTaskTypePrerequisite,
    CustomTaskTypeRequiredFor,
    CustomTaskTypeSupersede,
    Employee,
    Facility,
    Responsibility,
    Task,
    TaskHistory,
    TaskHistoryCertificate,
    TaskHistoryCertificatePage,
    TaskHistoryStatus,
    TrainingEvent,
)

import tests.factories as f
import tests.helpers as h
from tests.factories import (
    CustomTaskTypeFactory,
    EmployeeFactory,
    FacilityFactory,
    PositionFactory,
    ResponsibilityEducationRequirementFactory,
    ResponsibilityFactory,
    TaskFactory,
    TaskHistoryCertificateFactory,
    TaskHistoryFactory,
    TaskTypeEducationCreditFactory,
    TaskTypeFactory,
    TrainingEventFactory,
    login,
    logout,
)
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


def staff_subscription():
    f.SubscriptionFactory(
        facility=FacilityFactory(),
        status=Subscription.Status.trialing,
        billing_interval__plan__module=Plan.Module.staff,
        trial_end=timezone.now() + timedelta(days=1),
    )


class EmployeeViewTests(APITestCase):
    @login
    def setUp(self):
        self.same_fac_employee = EmployeeFactory()
        self.other_fac_employee = EmployeeFactory(facility__name="other fac")
        staff_subscription()

    def get_employee(self, pk):
        return self.client.get(reverse("employee-detail", kwargs={"pk": pk}))

    @logout
    def test_needs_auth(self):
        response = self.client.get(reverse("employee-list"))
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_requires_trial_staff_subscription(self):
        Subscription.objects.all().delete()
        r = self.client.get(reverse("employee-list"))
        h.responseForbidden(r)
        assert r.data["detail"] == "trial_staff_subscription_required"

    def test_dont_require_trial_staff_subscription_if_fcc_signup(self):
        Subscription.objects.all().delete()
        facility = self.logged_in_facility
        facility.fcc_signup = True
        facility.save()
        r = self.client.get(reverse("employee-list"))
        h.responseOk(r)

    def test_requires_staff_subscription_if_too_many_employees(self):
        f.EmployeeFactory.create_batch(
            FacilityHasStaffSubscriptionIfRequired.max_free_employee_count + 1,
            facility=self.logged_in_facility,
        )
        Subscription.objects.all().update(trial_end=timezone.now() - timedelta(days=1))
        r = self.client.get(reverse("employee-list"))
        h.responseForbidden(r)
        assert r.data["detail"] == "staff_subscription_required"

    def test_only_employee_in_users_facility_in_list(self):
        response = self.client.get(reverse("employee-list"))
        self.assertEqual(1, len(response.data))

    def test_can_see_detail_for_same_facility_employee(self):
        response = self.get_employee(self.same_fac_employee.pk)
        self.assertEqual(self.same_fac_employee.first_name, response.data["first_name"])

    def test_cant_see_detail_for_other_facility_employee(self):
        response = self.get_employee(self.other_fac_employee.pk)
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_an_employee_has_a_full_name(self):
        employee = EmployeeFactory(first_name="John", last_name="Smith")
        employee = self.get_employee(employee.pk).data
        self.assertEqual("John Smith", employee["full_name"])

    def test_can_search_by_full_name(self):
        found = EmployeeFactory(first_name="John", last_name="Smith")
        EmployeeFactory(first_name="john", last_name="kint")

        employees = self.client.get(reverse("employee-list"), {"full_name": "john sm"}).data

        self.assertEqual(1, len(employees))
        self.assertEqual(found.id, employees[0]["id"])

    def test_logged_employee_see_detail(self):
        user = f.UserFactory()
        found = EmployeeFactory(first_name="John", last_name="Smith", user=user)
        self.client.force_authenticate(user=user)
        employee = self.client.get(reverse("employee-me")).data
        self.assertEqual(found.user.id, employee["user"])

    def test_multiple_employee_invite(self):
        employee1 = EmployeeFactory(first_name="John", last_name="Smith", email="jhonsmith@foo.com")
        employee2 = EmployeeFactory(first_name="John", last_name="Doe", email="jhondoe@foo.com")
        employee3 = EmployeeFactory(first_name="John", last_name="Doe 2", email="jhondoe2@foo.com")
        f.UserInviteFactory(employee=employee3, email=employee3.email)
        res = self.client.post(
            reverse("employee-invite"),
            {"employees": [employee1.pk, employee2.pk, employee3.pk]},
        )
        h.responseOk(res)

        assert len(res.data["invited"]) == 2
        assert len(res.data["not_invited"]) == 1


class TestEmployeeViewTests(ApiMixin):
    view_name = "employee-list"

    def test_manager_cant_see_employees_if_not_allowed(
        self, manager_client, resident_and_staff_subscription
    ):
        facility_user = manager_client.user.facility_users
        facility_user.can_see_staff = False
        facility_user.save()

        r = manager_client.get(self.reverse())
        h.responseForbidden(r)


class EmployeeViewsetActiveTests(APITestCase):
    @login
    def setUp(self):
        self.active = EmployeeFactory(is_active=True)
        self.inactive = EmployeeFactory(is_active=False)
        staff_subscription()

    def test_can_return_active_and_inactive_employees(self):
        employees = self.client.get(reverse("employee-list")).data
        self.assertEqual(len(employees), 2)

    def test_can_return_active_employees_only(self):
        employees = self.client.get(reverse("employee-list"), {"is_active": True}).data
        employee_ids = [e["id"] for e in employees]
        self.assertEqual(len(employees), 1)
        self.assertIn(self.active.pk, employee_ids)

    def test_can_return_inactive_employees(self):
        employees = self.client.get(reverse("employee-list"), {"is_active": False}).data

        employee_ids = [e["id"] for e in employees]

        self.assertIn(self.inactive.pk, employee_ids)

    def test_can_return_inactive_employee(self):
        employee = self.client.get(
            reverse("employee-detail", kwargs={"pk": self.inactive.pk}),
            {"is_active": False},
        ).data

        self.assertEqual(employee["id"], self.inactive.pk)


class EmployeeLinkedToUserTests(APITestCase):
    @login
    def setUp(self):
        self.linked = EmployeeFactory(is_active=True, user=f.UserFactory())
        self.not_linked = EmployeeFactory(is_active=False, user=None)
        staff_subscription()

    def test_can_filter_employees_by_linked(self):
        employees = self.client.get(reverse("employee-list"), {"not_linked": True}).data

        employee_ids = [e["id"] for e in employees]
        self.assertIn(self.not_linked.pk, employee_ids)

        employees = self.client.get(reverse("employee-list"), {"not_linked": False}).data

        employee_ids = [e["id"] for e in employees]
        self.assertIn(self.linked.pk, employee_ids)


class EmployeeAddTests(APITestCase):
    @login
    def setUp(self):
        position = PositionFactory()
        self.data = {
            "first_name": "John",
            "last_name": "Snow",
            "ssn": "665-12-4567",
            "phone_number": "905-123-4567",
            "address": "123 fake street",
            "date_of_hire": "2014-1-1",
            "positions": [position.pk],
        }
        staff_subscription()

    def add_employee(self):
        return self.client.post(reverse("employee-list"), self.data)

    def test_can_add(self):
        response = self.add_employee()
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(self.data["first_name"], response.data["first_name"])

    def test_employee_creation_is_tracked(self):
        response = self.add_employee()
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(Activity.objects.count(), 1)
        activity = Activity.objects.get()
        employee = Employee.objects.get()
        self.assertEqual(activity.actor, self.logged_in_as)
        self.assertEqual(activity.verb, "created employee")
        self.assertEqual(activity.action_object, employee)
        self.assertEqual(activity.target, self.logged_in_facility)

    def test_has_same_facility_as_me(self):
        FacilityFactory(name="That other one")
        response = self.add_employee()

        employee = Employee.objects.get(pk=response.data["id"])
        self.assertEqual(self.logged_in_facility, employee.facility)

    def test_can_specify_positions(self):
        position = PositionFactory()
        self.data["positions"] = [position.id]
        response = self.add_employee()
        employee = Employee.objects.get(pk=response.data["id"])

        positions = employee.positions.all()
        self.assertEqual(1, len(positions))
        self.assertEqual(position, positions[0])

    def test_can_specify_responsibilities(self):
        responsibility = ResponsibilityFactory()
        self.data["other_responsibilities"] = [responsibility.id]
        response = self.add_employee()
        employee = Employee.objects.get(pk=response.data["id"])

        other_responsibilities = employee.other_responsibilities.all()
        self.assertEqual(1, len(other_responsibilities))
        self.assertEqual(responsibility, other_responsibilities[0])

    def test_can_specify_completed_tasks(self):
        task_type = TaskTypeFactory()
        self.data["completed_tasks"] = [{"type_id": task_type.id, "completion_date": "2014-1-1"}]

        response = self.add_employee()
        employee_id = response.data["id"]

        completed_tasks = TaskHistory.objects.filter(
            employee_id=employee_id, status=TaskHistoryStatus.completed, type=task_type
        )
        self.assertEqual(1, len(completed_tasks))
        self.assertEqual(date(2014, 1, 1), completed_tasks[0].completion_date)

    def test_pretty_phone_number(self):
        self.data["phone_number"] = "1234567890"
        employee = self.add_employee().data
        self.assertEqual("(123) 456-7890", employee["phone_number"])

    def test_pretty_ssn(self):
        self.data["ssn"] = "665124567"
        employee = self.add_employee().data
        self.assertEqual("665-12-4567", employee["ssn"])

    def test_ssn_is_not_required(self):
        self.data.pop("ssn")
        response = self.add_employee()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_phone_is_not_required(self):
        self.data.pop("phone_number")
        response = self.add_employee()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_must_have_at_least_one_position(self):
        self.data.pop("positions")
        response = self.add_employee()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EmployeeUpdateTests(APITestCase):
    @login
    def setUp(self):
        self.employee = EmployeeFactory()
        position = PositionFactory()
        self.employee.positions.add(position)
        self.employee_data = EmployeeReadSerializer(self.employee).data
        self.employee_data["positions"] = [p.pk for p in self.employee.positions.all()]
        self.employee_data.update(
            {
                "date_of_hire": "2014-10-31",
                "deactivation_date": None,
                "deactivation_reason": None,
            }
        )
        self.employee_data.pop("picture")
        staff_subscription()

    @logout
    def test_needs_auth(self):
        response = self.client.get(reverse("employee-detail", kwargs={"pk": self.employee.pk}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def update(self):
        return self.client.put(
            reverse("employee-detail", kwargs={"pk": self.employee.pk}),
            self.employee_data,
        )

    def test_update_employee_user_email(self):
        self.employee_data["email"] = "newemail@tester.com"
        self.assertEqual(status.HTTP_200_OK, self.update().status_code)
        self.assertEqual(
            "newemail@tester.com", Employee.objects.get(pk=self.employee.pk).user.email
        )

    def test_can_update_unchanged(self):
        self.employee_data["date_of_hire"] = date(2014, 1, 1)
        self.assertEqual(status.HTTP_200_OK, self.update().status_code)

    def test_can_hire_with_posthire_tasks_open(self):
        TaskFactory(employee=self.employee, type__required_within="2 weeks")

        status_code = self.update().status_code
        self.assertEqual(status.HTTP_200_OK, status_code)

    def test_can_hire_with_prehire_tasks_completed(self):
        TaskFactory(employee=self.employee, type__required_within=timedelta()).complete(
            date(2014, 1, 1)
        )
        status_code = self.update().status_code
        self.assertEqual(status.HTTP_200_OK, status_code)

    def test_can_force_hire_with_prehire_tasks_open(self):
        TaskFactory(employee=self.employee, type__required_within=timedelta())
        self.employee_data["force_hire"] = True

        status_code = self.update().status_code
        self.assertEqual(status.HTTP_200_OK, status_code)

    def test_pretty_phone_number(self):
        self.employee_data["phone_number"] = "1234567890"
        employee = self.update().data
        self.assertEqual("(123) 456-7890", employee["phone_number"])

    def test_pretty_ssn(self):
        self.employee_data["ssn"] = "665124567"
        employee = self.update().data
        self.assertEqual("665-12-4567", employee["ssn"])

    def test_positions_field_is_required_for_put_requests(self):
        self.employee_data.pop("positions")
        response = self.update()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_not_have_empty_positions(self):
        self.employee_data["positions"] = []
        response = self.update()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_patch_without_positions(self):
        target = reverse("employee-detail", kwargs={"pk": self.employee.pk})
        response = self.client.patch(target, {"first_name": "Test"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ResponsibilityViewTests(APITestCase):
    @login
    def setUp(self):
        staff_subscription()

    @logout
    def test_needs_auth(self):
        response = self.client.get(reverse("responsibility-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_responsibility_includes_positions(self):
        responsibility = ResponsibilityFactory()
        position = PositionFactory(name="Position")
        position.responsibilities.set([responsibility])

        data = self.client.get(
            reverse("responsibility-detail", kwargs={"pk": responsibility.pk})
        ).data
        self.assertEqual("Position", data["positions"][0]["name"])

    def create_responsibility(self, data):
        return self.client.post(reverse("responsibility-list"), data)

    def test_can_create_responsibility(self):
        data = {"name": "test"}
        response = self.create_responsibility(data)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_can_create_responsibility_with_positions(self):
        position = PositionFactory()
        data = {"name": "test", "positions": [position.pk]}
        response = self.create_responsibility(data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        responsibility = Responsibility.objects.all()[0]
        self.assertEqual(1, len(responsibility.position_set.all()))

    def edit_responsibility(self, pk, data):
        return self.client.put(reverse("responsibility-detail", kwargs={"pk": pk}), data)

    def test_can_edit_responsibility_with_no_facility_if_superuser(self):
        self.logged_in_as.is_superuser = True
        self.client.force_authenticate(self.logged_in_as)
        responsibility = ResponsibilityFactory(name="old name", facility=None)
        data = {"name": "new name"}
        response = self.edit_responsibility(responsibility.pk, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cant_edit_responsibility_with_no_facility_if_not_superuser(self):
        responsibility = ResponsibilityFactory(name="old name", facility=None)
        data = {"name": "new name"}
        response = self.edit_responsibility(responsibility.pk, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_edit_responsibility_with_same_facility(self):
        responsibility = ResponsibilityFactory(name="old name", facility=self.logged_in_facility)
        data = {"name": "new name"}
        response = self.edit_responsibility(responsibility.pk, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual("new name", Responsibility.objects.get(pk=responsibility.pk).name)

    def test_cant_edit_responsibility_with_other_facility(self):
        responsibility = ResponsibilityFactory(name="old name", facility__name="other")
        data = {"name": "new name"}
        response = self.edit_responsibility(responsibility.pk, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_edit_responsibility_positions(self):
        old_p = PositionFactory()
        new_p = PositionFactory()
        responsibility = ResponsibilityFactory(facility=self.logged_in_facility)
        responsibility.position_set.set([old_p])
        responsibility.save()
        data = {"name": responsibility.name, "positions": [new_p.pk]}
        self.edit_responsibility(responsibility.pk, data)

        edited = Responsibility.objects.get(pk=responsibility.pk)
        self.assertEqual(1, len(edited.position_set.all()))
        self.assertEqual(new_p, edited.position_set.all()[0])

    def test_only_list_same_or_none_facility(self):
        same = ResponsibilityFactory(name="same", facility=self.logged_in_facility)
        none = ResponsibilityFactory(name="none", facility=None)
        ResponsibilityFactory(name="other", facility__name="other")

        responsibilities = self.client.get(reverse("responsibility-list")).data
        names = [r["name"] for r in responsibilities]

        self.assertEqual(2, len(names))
        self.assertIn(same.name, names)
        self.assertIn(none.name, names)


class PositionViewTests(APITestCase):
    @login
    def setUp(self):
        staff_subscription()

    @logout
    def test_needs_auth(self):
        response = self.client.get(reverse("position-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaskTypeViewTests(APITestCase):
    @login
    def setUp(self):
        staff_subscription()

    @logout
    def test_needs_auth(self):
        response = self.client.get(reverse("tasktype-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_view_has_required_for(self):
        responsibility = ResponsibilityFactory()
        task_type = TaskTypeFactory()
        task_type.required_for.set([responsibility])
        task_type.save()

        response = self.client.get(reverse("tasktype-list"))
        task_types = response.data

        required_for = task_types[0]["required_for"]
        self.assertEqual(1, len(required_for))
        self.assertEqual(responsibility.name, required_for[0]["name"])

    def test_list_view_has_external_training_url(self):
        task_type = TaskTypeFactory(external_training_url="https://example.com/")

        response = self.client.get(reverse("tasktype-list"))
        task_types = response.data
        self.assertEqual(task_types[0]["external_training_url"], task_type.external_training_url)

    def test_includes_globals(self):
        TaskTypeFactory(facility=None)
        task_types = self.client.get(reverse("tasktype-list")).data
        self.assertEqual(1, len(task_types))

    def test_has_is_continuing_education_field(self):
        def d(pk):
            return self.client.get(reverse("tasktype-detail", kwargs={"pk": pk})).data[
                "is_continuing_education"
            ]

        yes = TaskTypeEducationCreditFactory().tasktype
        no = TaskTypeFactory()

        self.assertTrue(d(yes.pk))
        self.assertFalse(d(no.pk))

    def test_validity_period_is_not_required_for_one_off_task(self):
        data = {
            "name": "El Tasko",
            "is_one_off": True,
            "required_within": "1 day",
            "required_for": [ResponsibilityFactory().pk],
        }
        response = self.client.post(reverse("tasktype-list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_validity_period_is_required_for_non_one_off_task(self):
        data = {
            "name": "El Tasko",
            "required_within": "1 day",
            "required_for": [ResponsibilityFactory().pk],
        }

        response = self.client.post(reverse("tasktype-list"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data["validity_period"] = "1 day"

        response = self.client.post(reverse("tasktype-list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class CustomTaskTypeListTests(APITestCase):
    @login
    def setUp(self):
        staff_subscription()

    @logout
    def test_needs_auth(self):
        response = self.client.get(reverse("custom-task-types-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_shows(self):
        custom_task_type = CustomTaskTypeFactory(is_request=False)
        prerequisite = TaskTypeFactory()
        supersede = TaskTypeFactory()
        responsibility = ResponsibilityFactory()

        CustomTaskTypeRequiredFor.objects.create(
            custom_task_type=custom_task_type, required_for=responsibility
        )
        CustomTaskTypePrerequisite.objects.create(
            custom_task_type=custom_task_type, prerequisite=prerequisite
        )
        CustomTaskTypeSupersede.objects.create(
            custom_task_type=custom_task_type, supersede=supersede
        )

        response = self.client.get(reverse("custom-task-types-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data))
        self.assertEqual(1, len(response.data[0]["required_for"]))
        self.assertEqual(1, len(response.data[0]["prerequisites"]))
        self.assertEqual(1, len(response.data[0]["supersedes"]))


class TestCustomTaskTypeRequest(object):
    def test_needs_auth(self, client):
        staff_subscription()
        r = client.post(reverse("custom-task-types-request"))
        h.responseUnauthorized(r)

    def test_required_data(self, account_admin_client):
        staff_subscription()
        r = account_admin_client.post(reverse("custom-task-types-request"))
        h.responseBadRequest(r)
        assert {
            "validity_period",
            "required_within",
            "description",
            "name",
            "prerequisites",
            "supersedes",
            "required_for",
        } == set(r.data.keys())

    def test_sends_request_email(self, account_admin_client, outbox):
        staff_subscription()
        prerequesite = TaskTypeFactory()
        supersede = TaskTypeFactory()
        responsibility = ResponsibilityFactory()
        data = {
            "name": "New custom task type",
            "required_within": "2 weeks",
            "validity_period": "2 weeks",
            "prerequisites": [prerequesite.id],
            "supersedes": [supersede.id],
            "description": "New custom task type",
            "required_for": [responsibility.id],
        }
        r = account_admin_client.post(reverse("custom-task-types-request"), data)
        h.responseCreated(r)
        assert CustomTaskTypePrerequisite.objects.count() == 1
        assert CustomTaskTypeSupersede.objects.count() == 1
        assert CustomTaskTypeRequiredFor.objects.count() == 1
        assert len(outbox) == 1
        assert outbox[0].to == [settings.CUSTOM_TASK_TYPE_ADMIN_EMAIL]

    def test_sets_is_request(self, account_admin_client):
        staff_subscription()
        data = {
            "name": "New custom task type",
            "required_within": "2 weeks",
            "validity_period": "2 weeks",
            "prerequisites": [],
            "supersedes": [],
            "description": "New custom task type",
            "required_for": [],
        }
        r = account_admin_client.post(reverse("custom-task-types-request"), data)
        h.responseCreated(r)
        custom_task_type = CustomTaskType.objects.get()
        assert custom_task_type.is_request


class TaskViewTests(APITestCase):
    @login
    def setUp(self):
        staff_subscription()

    @logout
    def test_needs_auth(self):
        response = self.client.get(reverse("task-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @logout
    def test_needs_auth_me(self):
        response = self.client.get(reverse("task-me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_shows(self):
        TaskFactory()
        response = self.client.get(reverse("task-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_employee_list_tasks(self):
        user = f.UserFactory()
        employee = f.EmployeeFactory(user=user)
        TaskFactory.create_batch(size=3, employee=employee)
        TaskFactory()
        self.client.force_authenticate(user=user)
        response = self.client.get(reverse("task-me"))
        h.responseOk(response)
        self.assertEqual(len(response.data), 3)

    def test_does_not_show_inactive_users(self):
        TaskFactory()
        TaskFactory(employee__is_active=False)

        tasks = self.client.get(reverse("task-list")).data
        self.assertEqual(1, len(tasks))

    def test_can_create_task(self):
        task_type = TaskTypeFactory()
        employee = EmployeeFactory()
        data = {"type": task_type.id, "employee": employee.id, "status": 1}

        response = self.client.post(reverse("task-list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.data
        self.assertEqual(task_type.name, data["type_name"])

    def test_can_filter_on_days_till_due(self):
        within_limit = TaskFactory(due_date=date.today())
        TaskFactory(due_date=date.today() + timedelta(days=31))

        tasks = self.client.get(reverse("task-list"), {"due_date_limit": "30 days"}).data
        self.assertEqual(1, len(tasks))
        self.assertEqual(within_limit.id, tasks[0]["id"])

    def test_can_filter_on_language(self):
        task_type = f.TaskTypeFactory()
        f.CourseFactory(task_type=task_type, language=2)
        TaskFactory(type=task_type, due_date=date.today() + timedelta(days=31))

        tasks = self.client.get(reverse("task-list"), {"type__course__language": 1}).data
        self.assertEqual(0, len(tasks))

        tasks = self.client.get(reverse("task-list"), {"type__course__language": 2}).data
        self.assertEqual(1, len(tasks))

    def test_can_filter_me_on_language(self):
        user = f.UserFactory()
        employee = f.EmployeeFactory(user=user)
        task_types = f.TaskTypeFactory.create_batch(size=2)
        f.CourseFactory(task_type=task_types[0], language=2)
        f.CourseFactory(task_type=task_types[1], language=1)

        TaskFactory(type=task_types[0], employee=employee)
        TaskFactory(type=task_types[1], employee=employee)
        self.client.force_authenticate(user=user)
        response = self.client.get(
            reverse("task-me"), {"expand": "type.course", "type__course__language": 2}
        )
        h.responseOk(response)
        self.assertEqual(len(response.data), 1)
        assert response.data[0]["type"]["course"]["language"] == 2

    def test_can_filter_me_on_language_includes_trainings_without_course(self):
        user = f.UserFactory()
        employee = f.EmployeeFactory(user=user)
        task_types = f.TaskTypeFactory.create_batch(size=3)
        f.CourseFactory(task_type=task_types[0], language=2)
        f.CourseFactory(task_type=task_types[1], language=1)
        f.CourseFactory()

        TaskFactory(type=task_types[0], employee=employee)
        TaskFactory(type=task_types[1], employee=employee)
        TaskFactory(type=task_types[2], employee=employee)
        self.client.force_authenticate(user=user)
        response = self.client.get(
            reverse("task-me"), {"expand": "type.course", "type__course__language": 1}
        )
        h.responseOk(response)
        self.assertEqual(len(response.data), 2)
        assert response.data[0]["type"]["course"]["language"] == 1

    def test_scheduled_for_non_scheduled_task(self):
        task = TaskFactory()
        task = self.client.get(reverse("task-detail", kwargs={"pk": task.pk})).data
        self.assertIsNone(task["scheduled_event"])

    def test_take_online_course_task(self):
        user = f.UserFactory()
        employee = f.EmployeeFactory(user=user)
        task_type = f.TaskTypeFactory()
        f.CourseFactory(task_type=task_type, published=True)
        TaskFactory(type=task_type, employee=employee)
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse("task-me"))
        h.responseOk(response)

        self.assertEqual(response.data[0]["online_course"], True)

    def test_trainings_users_should_return_user_employee_tasks(self):
        user = f.UserFactory()
        f.FacilityUserFactory(user=user, role=FacilityUser.Role.trainings_user)
        employee = f.EmployeeFactory(user=user)
        task_types = f.TaskTypeFactory.create_batch(size=3)

        employee2 = f.EmployeeFactory()

        TaskFactory(type=task_types[0], employee=employee)
        TaskFactory(type=task_types[1], employee=employee)
        TaskFactory(type=task_types[2], employee=employee)

        TaskFactory(type=task_types[0], employee=employee2)
        TaskFactory(type=task_types[1], employee=employee2)
        TaskFactory(type=task_types[2], employee=employee2)
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse("task-list"))

        h.responseOk(response)

        self.assertEqual(len(response.data), 3)

    def test_manager_users_without_staff_permissions_can_only_see_their_tasks(self):
        user = f.UserFactory()
        f.FacilityUserFactory(user=user, role=FacilityUser.Role.manager, can_see_staff=False)
        employee = f.EmployeeFactory(user=user)
        task_types = f.TaskTypeFactory.create_batch(size=3)

        employee2 = f.EmployeeFactory()

        TaskFactory(type=task_types[0], employee=employee)
        TaskFactory(type=task_types[1], employee=employee)
        TaskFactory(type=task_types[2], employee=employee)

        TaskFactory(type=task_types[0], employee=employee2)
        TaskFactory(type=task_types[1], employee=employee2)
        TaskFactory(type=task_types[2], employee=employee2)
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse("task-list"))

        h.responseOk(response)

        self.assertEqual(len(response.data), 3)

    def test_manager_users_with_staff_permissions_can_see_all_employee_tasks(self):
        user = f.UserFactory()
        f.FacilityUserFactory(user=user, role=FacilityUser.Role.manager, can_see_staff=True)
        employee = f.EmployeeFactory(user=user)
        task_types = f.TaskTypeFactory.create_batch(size=3)

        employee2 = f.EmployeeFactory()

        TaskFactory(type=task_types[0], employee=employee)
        TaskFactory(type=task_types[1], employee=employee)
        TaskFactory(type=task_types[2], employee=employee)

        TaskFactory(type=task_types[0], employee=employee2)
        TaskFactory(type=task_types[1], employee=employee2)
        TaskFactory(type=task_types[2], employee=employee2)
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse("task-list"))

        h.responseOk(response)

        self.assertEqual(len(response.data), 6)

    def test_scheduled_for_scheduled_task(self):
        task = TaskFactory()
        event = TrainingEventFactory(training_for=task.type, attendees=[task.employee])
        task = self.client.get(reverse("task-detail", kwargs={"pk": task.pk})).data
        self.assertEqual(event.start_time.date(), task["scheduled_event"]["date"].date())
        self.assertEqual(event.pk, task["scheduled_event"]["id"])


class TestTaskHistoryView:
    @pytest.fixture
    def data(self):
        self.task = TaskFactory()
        return {
            "type": self.task.type.id,
            "employee": self.task.employee.id,
            "completion_date": "2014-1-1",
            "status": TaskHistoryStatus.completed,
        }

    def test_needs_auth(self, client):
        response = client.get(reverse("taskhistory-list"))
        h.responseUnauthorized(response)

    def test_needs_auth_me(self, client):
        response = client.get(reverse("taskhistory-me"))
        h.responseUnauthorized(response)

    def test_employee_list_task_histories(self, client):
        user = f.UserFactory()
        employee = f.EmployeeFactory(user=user)
        TaskHistoryFactory.create_batch(size=3, employee=employee)
        TaskHistoryFactory()
        client.force_authenticate(user=user)
        response = client.get(reverse("taskhistory-me"))
        h.responseOk(response)
        assert len(response.data) == 3

    def test_create_and_complete_task(self, account_admin_client, data):
        staff_subscription()
        with patch.object(Task, "complete") as mock:
            mock.return_value = TaskHistoryFactory()
            response = account_admin_client.post(reverse("taskhistory-list"), data)
        h.responseCreated(response)
        assert mock.called
        assert TaskHistory.objects.count() == 1

    def test_create_and_complete_task_with_certificate(self, account_admin_client, data, pdf_file):
        staff_subscription()
        with patch.object(Task, "complete") as mock:
            mock.return_value = TaskHistoryFactory()
            tmp_file = tempfile.NamedTemporaryFile(suffix=".pdf")
            with open(tmp_file.name, "wb") as certificate_page:
                certificate_page.write(pdf_file)
            tmp_file_2 = tempfile.NamedTemporaryFile(suffix=".pdf")
            with open(tmp_file_2.name, "wb") as certificate_page:
                certificate_page.write(pdf_file)
            data["certificate1"] = tmp_file
            data["certificate2"] = tmp_file_2
            response = account_admin_client.post(
                reverse("taskhistory-list"), data, format="multipart"
            )
        h.responseCreated(response)
        assert mock.called
        assert TaskHistory.objects.count() == 1
        assert TaskHistoryCertificate.objects.count() == 1
        assert TaskHistoryCertificatePage.objects.count() == 2

    def test_can_upload_certificate_for_existing_task_history(self, account_admin_client, pdf_file):
        staff_subscription()
        task_history = TaskHistoryFactory()
        tmp_file = tempfile.NamedTemporaryFile(suffix=".pdf")
        with open(tmp_file.name, "wb") as certificate_page:
            certificate_page.write(pdf_file)
        response = account_admin_client.post(
            reverse("taskhistory-certificate", kwargs={"pk": task_history.id}),
            {"certificate1": tmp_file},
            format="multipart",
        )
        h.responseOk(response)
        assert TaskHistoryCertificate.objects.count() == 1

    def test_can_delete_certificate_of_task_history(self, account_admin_client):
        staff_subscription()
        task_history_certificate = TaskHistoryCertificateFactory()
        response = account_admin_client.delete(
            reverse(
                "taskhistory-certificate",
                kwargs={"pk": task_history_certificate.task_history.id},
            )
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert TaskHistoryCertificate.objects.count() == 0

    def test_returns_404_if_task_history_has_no_certificate(self, account_admin_client):
        staff_subscription()
        task_history = TaskHistoryFactory()
        response = account_admin_client.delete(
            reverse("taskhistory-certificate", kwargs={"pk": task_history.id})
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize("file_type", [".pdf", ".png", ".jpg"])
    def test_returns_certificate_with_correct_extension_and_content_type(
        self, account_admin_client, file_type, pdf_file
    ):
        staff_subscription()
        task_history = TaskHistoryFactory()
        tmp_file = tempfile.NamedTemporaryFile(suffix=file_type)
        with open(tmp_file.name, "wb") as certificate_page:
            certificate_page.write(pdf_file)
        account_admin_client.post(
            reverse("taskhistory-certificate", kwargs={"pk": task_history.id}),
            {"certificate1": tmp_file},
            format="multipart",
        )

        response = account_admin_client.get(
            reverse("taskhistory-certificate", kwargs={"pk": task_history.id})
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.get("Content-Disposition")[-5:-1] == file_type
        assert response.get("Content-Type") == mimetypes.types_map[file_type]

    def test_requires_credit_hours_if_has_continuing_ed(self, account_admin_client, data):
        staff_subscription()
        TaskTypeEducationCreditFactory(tasktype=self.task.type)
        response = account_admin_client.post(reverse("taskhistory-list"), data)
        h.responseBadRequest(response)

    def test_can_specify_credit_hours(self, account_admin_client, data):
        staff_subscription()
        TaskTypeEducationCreditFactory(tasktype=self.task.type)
        data["credit_hours"] = 5
        response = account_admin_client.post(reverse("taskhistory-list"), data)
        th = response.data
        assert 5 == th["credit_hours"]


class TrainingEventTests(APITestCase):
    @login
    def setUp(self):
        staff_subscription()

    @logout
    def test_needs_auth(self):
        response = self.client.get(reverse("trainingevent-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_passes_along_incomplete_attendees(self):
        event = TrainingEventFactory()
        # Doesn't actually exist, but we don't care.
        attendee_id = 1

        with patch.object(TrainingEvent, "finish") as mock:
            data = {"incomplete_attendees": [attendee_id]}
            self.client.post(reverse("trainingevent-finish", kwargs={"pk": event.pk}), data)
            mock.assert_called_with([attendee_id], 0)

    def test_passes_along_credit_hours(self):
        edu = TaskTypeEducationCreditFactory(tasktype__is_training=True)
        event = TrainingEventFactory(training_for=edu.tasktype)

        credit_hours = 4.5
        data = {"credit_hours": credit_hours}

        with patch.object(TrainingEvent, "finish") as mock:
            self.client.post(reverse("trainingevent-finish", kwargs={"pk": event.pk}), data)
            mock.assert_called_with([], credit_hours)

    def test_has_training_for_name(self):
        event = TrainingEventFactory()

        events = self.client.get(reverse("trainingevent-list")).data
        self.assertEqual(event.training_for.name, events[0]["training_for_name"])

    def test_has_a_flyer_url(self):
        event = TrainingEventFactory()
        event = self.client.get(reverse("trainingevent-detail", kwargs={"pk": event.pk})).data
        self.assertIn("flyer_url", event)

    def test_training_event_created_has_facility_of_user(self):
        task_type = TaskTypeFactory(is_training=True)

        data = {
            "training_for": task_type.pk,
            "start_time": timezone.now(),
            "end_time": timezone.now(),
            "location": "Cebu",
        }

        response = self.client.post(reverse("trainingevent-list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        admin_user_facility_id = Facility.objects.get().pk
        self.assertEqual(response.data["facility"], admin_user_facility_id)


class ComplianceViewTests(APITestCase):
    @login
    def setUp(self):
        staff_subscription()

    @logout
    def test_needs_auth(self):
        response = self.client.get(reverse("compliance"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ResponsibilityEducationRequirementTests(APITestCase):
    @login
    def setUp(self):
        staff_subscription()

    @logout
    def test_needs_auth(self):
        response = self.client.get(reverse("responsibilityeducationrequirement-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_read_has_responsibility_object(self):
        req = ResponsibilityEducationRequirementFactory()
        responsibility = req.responsibility

        req = self.client.get(
            reverse("responsibilityeducationrequirement-detail", kwargs={"pk": req.pk})
        ).data
        self.assertEqual(responsibility.name, req["responsibility"]["name"])

    def test_read_has_interval_base_object(self):
        req = ResponsibilityEducationRequirementFactory()
        interval_base = req.interval_base

        req = self.client.get(
            reverse("responsibilityeducationrequirement-detail", kwargs={"pk": req.pk})
        ).data
        self.assertEqual(interval_base.name, req["interval_base"]["name"])

    def test_read_has_type_name(self):
        req = ResponsibilityEducationRequirementFactory()
        req = self.client.get(
            reverse("responsibilityeducationrequirement-detail", kwargs={"pk": req.pk})
        ).data
        self.assertEqual("Any", req["type_name"])
