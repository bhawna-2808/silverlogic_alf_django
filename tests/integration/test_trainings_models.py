from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

import pytest
from mock import patch

from apps.trainings.models import (
    Antirequisite,
    Employee,
    Facility,
    FacilityDefault,
    Task,
    TaskHistory,
    TaskHistoryStatus,
    TaskStatus,
)

import tests.factories as f

pytestmark = pytest.mark.django_db


class TestEmployee:
    def test_deleted_employee_still_exists(self):
        employee = f.EmployeeFactory()
        assert Employee.objects.count() == 1
        employee.delete()
        assert Employee.objects.count() == 1

    def test_deleted_employee_is_inactive(self):
        employee = f.EmployeeFactory()
        employee.delete()
        assert not employee.is_active

    def test_bulk_deleted_employees_still_exist(self):
        f.EmployeeFactory()
        f.EmployeeFactory()
        assert Employee.objects.count() == 2
        Employee.objects.all().delete()
        assert Employee.objects.count() == 2

    def test_bulk_deleted_employees_are_inactive(self):
        f.EmployeeFactory()
        f.EmployeeFactory()
        Employee.objects.all().delete()
        for employee in Employee.objects.all():
            assert not employee.is_active

    def test_name_is_prettified(self):
        employee = f.EmployeeFactory(first_name="jOnAs", last_name="fLINt")
        assert employee.first_name == "Jonas"
        assert employee.last_name == "Flint"

    def test_no_antirequisite_task_is_created_for_employee(self):
        """
        If a task type is required for a `Responsibility` but that task type is
        also an antirequisite that is not applicable to the employee, then
        a task of that type shouldn't be added to the employee
        """
        position = f.PositionFactory()
        responsibility = f.ResponsibilityFactory()
        position.responsibilities.add(responsibility)
        task_type = f.TaskTypeFactory()
        task_type.required_for.add(responsibility)
        f.AntirequisiteFactory(task_type=task_type, valid_after_hire_date=date(2014, 1, 5))
        employee = f.EmployeeFactory(date_of_hire=date(2014, 1, 4))
        employee.positions.add(position)
        task_types_pks = employee.trainings_task_set.values_list("type__pk", flat=True)
        assert task_type.pk not in task_types_pks

    def test_employee_deactivation_date_behaviour(self):
        employee = f.EmployeeFactory(is_active=True, deactivation_date=None)
        employee.deactivation_date = date.today() - timedelta(days=1)
        employee.save()
        employee.refresh_from_db()
        assert not employee.is_active
        employee.is_active = True
        employee.save()
        employee.refresh_from_db()
        employee.deactivation_date = None
        employee.save()
        employee.refresh_from_db()
        assert employee.is_active


class TestTask:
    def test_cannot_bulk_create(self):
        with pytest.raises(RuntimeError):
            Task.objects.bulk_create([Task()])

    def test_duplicate_task_chooses_earlier_due_date(self):
        employee = f.EmployeeFactory()
        task_type = f.TaskTypeFactory()
        f.TaskFactory(employee=employee, type=task_type, due_date=date(2014, 1, 2))
        f.TaskFactory(employee=employee, type=task_type, due_date=date(2014, 1, 1))
        f.TaskFactory(employee=employee, type=task_type, due_date=date(2014, 1, 3))

        task = Task.objects.get(employee=employee, type=task_type)
        assert task.due_date == date(2014, 1, 1)

    def test_recompute_due_date_depends_on_facility_capacity(self):
        facility = f.FacilityFactory(capacity=1)
        task_type = f.TaskTypeFactory(facility=facility, min_capacity=2, max_capacity=3)
        task = f.TaskFactory(type=task_type)
        task.recompute_due_date()

        with pytest.raises(Task.DoesNotExist):
            task.refresh_from_db()


class TestTaskComplete:
    def test_creates_a_task_history(self):
        task = f.TaskFactory()
        task.complete(date(2014, 1, 1))
        assert TaskHistory.objects.count() == 1

    def test_is_one_off_does_not_create_new_task_when_completed(self):
        employee = f.EmployeeFactory()
        tasktype = f.TaskTypeFactory(is_one_off=True)
        task = f.TaskFactory(type=tasktype, employee=employee)
        taskhistory = task.complete(date.today())
        assert not Task.objects.filter(pk=task.id).exists()
        assert TaskHistory.objects.filter(pk=taskhistory.id).exists()

    def test_sets_history_completion_date(self):
        task = f.TaskFactory()
        th = task.complete(date(2014, 1, 1))
        assert th.completion_date == date(2014, 1, 1)

    def test_sets_history_expiration_date(self):
        task = f.TaskFactory(type__validity_period="2 weeks")
        th = task.complete(date(2014, 1, 1))
        # The completion date + the validity period.
        assert th.expiration_date == date(2014, 1, 15)

    def test_sets_history_status(self):
        task = f.TaskFactory()
        th = task.complete(date(2014, 1, 1))
        assert th.status == TaskHistoryStatus.completed

    def test_sets_new_due_date(self):
        task = f.TaskFactory(type__validity_period="3 days")
        task.complete(date(2014, 1, 5))
        assert task.due_date == date(2014, 1, 8)

    def test_sets_status_to_open(self):
        task = f.TaskFactory(status=TaskStatus.scheduled)
        task.complete(date(2014, 1, 1))
        assert task.status == TaskStatus.open

    def test_saves_the_changes(self):
        task = f.TaskFactory(status=TaskStatus.scheduled)
        with patch("apps.trainings.models.Task.save") as save:
            task.complete(date(2014, 1, 1))
            assert save.called

    def test_sets_credit_hours(self):
        type = f.TaskTypeEducationCreditFactory().tasktype
        task = f.TaskFactory(type=type)
        credit_hours = 3
        th = task.complete(date(2014, 1, 1), credit_hours)
        assert th.credit_hours == credit_hours

    def test_does_not_set_credit_hours_if_not_continuing_education(self):
        task = f.TaskFactory()
        credit_hours = 3
        th = task.complete(date(2014, 1, 1), credit_hours)
        assert th.credit_hours == 0


class TestTaskIncomplete:
    def test_creates_a_task_history(self):
        task = f.TaskFactory()
        task.incomplete(date(2014, 1, 1))
        assert TaskHistory.objects.count() == 1

    def test_sets_history_completion_date(self):
        task = f.TaskFactory()
        th = task.incomplete(date(2014, 1, 1))
        assert th.completion_date == date(2014, 1, 1)

    def test_doesnt_set_history_expiration_date(self):
        task = f.TaskFactory(type__validity_period="2 weeks")
        th = task.incomplete(date(2014, 1, 1))
        assert th.expiration_date is None

    def test_sets_history_status(self):
        task = f.TaskFactory()
        th = task.incomplete(date(2014, 1, 1))
        assert th.status == TaskHistoryStatus.incomplete

    def test_sets_status_to_open(self):
        task = f.TaskFactory(status=TaskStatus.scheduled)
        task.incomplete(date(2014, 1, 1))
        assert task.status == TaskStatus.open

    def test_saves_the_changes(self):
        task = f.TaskFactory(status=TaskStatus.scheduled)
        with patch("apps.trainings.models.Task.save") as save:
            task.incomplete(date(2014, 1, 1))
            assert save.called


class TaskDueDateUpdateOnEmployeeHireDateChangeTests(TestCase):
    def setUp(self):
        self.employee = f.EmployeeFactory()
        f.TaskFactory(employee=self.employee)
        f.TaskFactory(employee=self.employee)

    def check(self, expected_call_count):
        with patch.object(Task, "recompute_due_date") as mock:
            self.employee.save()
            self.assertEqual(expected_call_count, mock.call_count)

    def test_recalculates_when_date_of_hire_changed(self):
        self.employee.date_of_hire = timezone.now().date()
        self.check(2)

    def test_does_nothing_when_nothing_changed(self):
        self.check(0)


class TrainingEventFinishTests(TestCase):
    def test_training_event_complete_set(self):
        event = f.TrainingEventFactory()
        event.finish()
        self.assertTrue(event.completed)

    def test_task_completed_for_attendees(self):
        training_for = f.TaskTypeFactory()
        attendee = f.EmployeeFactory()
        f.TaskFactory(type=training_for, employee=attendee)
        event = f.TrainingEventFactory(training_for=training_for, attendees=[attendee])

        event.finish()
        # If we can get this object, then it worked.
        TaskHistory.objects.get(
            type=training_for, employee=attendee, status=TaskHistoryStatus.completed
        )

    def test_task_not_completed_for_non_attendees(self):
        task = f.TaskFactory()
        event = f.TrainingEventFactory(training_for=task.type)

        event.finish()
        self.assertEqual(0, len(TaskHistory.objects.all()))

    def test_task_is_incomplete_for_incomplete_attendees(self):
        training_for = f.TaskTypeFactory()
        attendee = f.EmployeeFactory()
        f.TaskFactory(type=training_for, employee=attendee)
        event = f.TrainingEventFactory(training_for=training_for, attendees=[attendee])

        event.finish([attendee.pk])
        # If we can get this object, then it worked.
        TaskHistory.objects.get(
            type=training_for, employee=attendee, status=TaskHistoryStatus.incomplete
        )


class TrainingEventFinishContinuingEdTests(TestCase):
    def setUp(self):
        d = timezone.now()
        self.hour = 3
        start_time = d.replace(hour=0, minute=0, second=0)
        end_time = d.replace(hour=self.hour, minute=0, second=0)

        task = f.TaskFactory(type__is_training=True)
        f.TaskTypeEducationCreditFactory(tasktype=task.type)
        self.event = f.TrainingEventFactory(
            training_for=task.type,
            attendees=[task.employee],
            start_time=start_time,
            end_time=end_time,
        )

    def test_can_autocalculate_credits(self):
        self.event.finish()
        history = TaskHistory.objects.all()[0]
        self.assertEqual(self.hour, history.credit_hours)

    def test_can_manually_give_credits(self):
        self.event.finish(credit_hours=5)
        history = TaskHistory.objects.all()[0]
        self.assertEqual(5, history.credit_hours)


class EmployeeTaskAutoCreationAndDeletionTests(TestCase):
    """Tasks are created/removed when employees gain/lose positions or responsibilities."""

    def setUp(self):
        self.employee = f.EmployeeFactory()

    def test_other_responsibility_added(self):
        responsibility = f.ResponsibilityFactory()
        f.TaskTypeFactory(required_for=[responsibility])

        self.employee.other_responsibilities.add(responsibility)

        self.assertEqual(1, len(Task.objects.filter(employee=self.employee)))

    def test_position_added(self):
        responsibility = f.ResponsibilityFactory()
        f.TaskTypeFactory(required_for=[responsibility])
        position = f.PositionFactory(responsibilities=[responsibility])

        self.employee.positions.add(position)

        self.assertEqual(1, len(Task.objects.filter(employee=self.employee)))

    def test_one_off_task_completed_then_responsibility_added(self):
        """The employee already satisfied the task so don't make it."""
        responsibility = f.ResponsibilityFactory()
        task = f.TaskFactory(
            type__is_one_off=True,
            type__required_for=[responsibility],
            employee=self.employee,
        )
        task.complete(date(2014, 1, 1))

        self.employee.other_responsibilities.add(responsibility)

        self.assertFalse(Task.objects.filter(employee=self.employee).exists())

    def test_other_responsibility_removed(self):
        responsibility = f.ResponsibilityFactory()
        f.TaskTypeFactory(required_for=[responsibility])
        self.employee.other_responsibilities.add(responsibility)
        self.employee.other_responsibilities.remove(responsibility)
        self.assertEqual(0, len(Task.objects.filter(employee=self.employee)))

    def test_other_responsibility_removed_does_not_effect_other_employees(self):
        responsibility = f.ResponsibilityFactory()
        f.TaskTypeFactory(required_for=[responsibility])

        other_employee = f.EmployeeFactory()
        other_employee.other_responsibilities.add(responsibility)

        self.employee.other_responsibilities.add(responsibility)
        self.employee.other_responsibilities.remove(responsibility)

        self.assertEqual(1, len(Task.objects.filter(employee=other_employee)))

    def test_position_removed(self):
        responsibility = f.ResponsibilityFactory()
        f.TaskTypeFactory(required_for=[responsibility])
        position = f.PositionFactory(responsibilities=[responsibility])
        self.employee.positions.add(position)
        self.employee.positions.remove(position)
        self.assertEqual(0, len(Task.objects.filter(employee=self.employee)))

    def test_optional_task_handled(self):
        responsibility = f.ResponsibilityFactory()
        task_type = f.TaskTypeFactory(required_for=[responsibility])
        task = f.TaskFactory(is_optional=True, type=task_type, employee=self.employee)
        position = f.PositionFactory(responsibilities=[responsibility])
        self.employee.positions.add(position)
        self.assertEqual(1, len(Task.objects.filter(employee=self.employee)))
        task.refresh_from_db()
        self.assertEqual(False, task.is_optional)

    def test_signal_creates_with_optional_false_if_non_existing_task(self):
        responsibility = f.ResponsibilityFactory()
        f.TaskTypeFactory(required_for=[responsibility])
        position = f.PositionFactory(responsibilities=[responsibility])
        self.employee.positions.add(position)
        self.assertEqual(1, len(Task.objects.filter(employee=self.employee)))
        self.assertEqual(False, Task.objects.filter(employee=self.employee).first().is_optional)


class TaskTypeAutoCreateTaskForEmployeeTests:
    """Tasks should be required when an employee gets a new position/responsibility"""

    def test_created_for_position_responsibilities(self):
        responsibility1 = f.ResponsibilityFactory()
        responsibility2 = f.ResponsibilityFactory()
        position = f.PositionFactory(responsibilities=[responsibility1, responsibility2])
        employee = f.EmployeeFactory(positions=[position])
        task_type = f.TaskTypeFactory(required_for=[responsibility1, responsibility2])
        tasks = Task.objects.filter(employee=employee, type=task_type)
        self.assertEqual(1, len(tasks))

    def test_created_for_other_responsibilities(self):
        responsibility = f.ResponsibilityFactory()
        task_type = f.TaskTypeFactory(required_for=[responsibility])
        employee = f.EmployeeFactory(other_responsibilities=[responsibility])
        tasks = Task.objects.filter(employee_id=employee, type=task_type)
        self.assertEqual(1, len(tasks))


class AllowedTaskTypeTests(TestCase):
    def test_no_prereq(self):
        f.TaskTypeFactory()
        employee = f.EmployeeFactory()
        self.assertEqual(1, len(employee.get_tasktypes_allowed_by_prerequisites()))

    def test_unfulfilled_prereq(self):
        f.TaskTypeFactory(prerequisites=[f.TaskTypeFactory()])
        employee = f.EmployeeFactory()
        # 1 because the prereq is also a task type, so there are 2.
        self.assertEqual(1, len(employee.get_tasktypes_allowed_by_prerequisites()))

    def test_partial_filled_prereq(self):
        prereq1 = f.TaskTypeFactory()
        f.TaskTypeFactory(prerequisites=[prereq1, f.TaskTypeFactory()])
        employee = f.EmployeeFactory()

        # Complete one of the prereqs
        f.TaskFactory(employee=employee, type=prereq1).complete(date(2014, 1, 1))

        self.assertEqual(2, len(employee.get_tasktypes_allowed_by_prerequisites()))

    def test_filled_prereq(self):
        prereq1 = f.TaskTypeFactory()
        prereq2 = f.TaskTypeFactory()
        f.TaskTypeFactory(prerequisites=[prereq1, prereq2])
        employee = f.EmployeeFactory()

        # Complete both the prereqs
        f.TaskFactory(employee=employee, type=prereq1).complete(date(2014, 1, 1))
        f.TaskFactory(employee=employee, type=prereq2).complete(date(2014, 1, 1))

        self.assertEqual(3, len(employee.get_tasktypes_allowed_by_prerequisites()))

    def test_ignore_self_prerequisite(self):
        tasktype = f.TaskTypeFactory()
        tasktype.prerequisites.set([tasktype])
        tasktype.save()
        allowed_tasktype_list = [
            t.id for t in f.EmployeeFactory().get_tasktypes_allowed_by_prerequisites()
        ]
        self.assertIn(tasktype.id, allowed_tasktype_list)

    def test_filled_but_expired_prereq(self):
        pass


class TaskSupersedeCompleteTests(TestCase):
    """In all these tests x supersedes y"""

    def x_supersedes_y(self, x_type_args={}, y_type_args={}, x_args={}, y_args={}):
        y_type = f.TaskTypeFactory(**y_type_args)
        x_type = f.TaskTypeFactory(supersedes=[y_type], **x_type_args)

        employee = f.EmployeeFactory()
        x = f.TaskFactory(type=x_type, employee=employee, **x_args)
        y = f.TaskFactory(type=y_type, employee=employee, **y_args)
        return x, y

    def complete_x_and_refresh_y(self, x, y):
        x.complete(timezone.now().date())
        return Task.objects.get(pk=y.pk)

    def test_complete_x_updates_y_due_date(self):
        x, y = self.x_supersedes_y(
            x_type_args=dict(validity_period="3 days"),
            y_type_args=dict(validity_period="5 days"),
        )
        y = self.complete_x_and_refresh_y(x, y)
        self.assertEqual(x.due_date, y.due_date)

    def test_complete_x_updates_y_status(self):
        x, y = self.x_supersedes_y(y_args=dict(status=TaskStatus.open))
        y = self.complete_x_and_refresh_y(x, y)
        self.assertEqual(TaskStatus.open, y.status)

    def test_complete_x_does_not_update_y_due_date(self):
        """When y due_date is greater than the updated x due_date."""
        y_due_date = timezone.now().date() + timedelta(days=4)
        x, y = self.x_supersedes_y(
            x_type_args=dict(validity_period="3 days"), y_args=dict(due_date=y_due_date)
        )
        y = self.complete_x_and_refresh_y(x, y)
        self.assertEqual(y_due_date, y.due_date)

    def test_delete_y_when_x_is_one_off(self):
        x, y = self.x_supersedes_y(x_type_args=dict(is_one_off=True))
        try:
            y = self.complete_x_and_refresh_y(x, y)
        except Task.DoesNotExist:
            pass
        else:
            self.assertTrue(False)

    def test_complete_x_does_not_delete_other_employee_y_for_one_off(self):
        x, y = self.x_supersedes_y(x_type_args=dict(is_one_off=True))
        other_employee = f.EmployeeFactory()
        other_y = f.TaskFactory(type=y.type, employee=other_employee)
        x.complete(timezone.now().date())
        Task.objects.get(pk=other_y.pk)

    def test_complete_x_does_not_update_other_employee_y_due_date(self):
        x, y = self.x_supersedes_y(
            x_type_args=dict(validity_period="3 days"),
            y_type_args=dict(validity_period="5 days"),
        )
        other_employee = f.EmployeeFactory()
        other_y = f.TaskFactory(type=y.type, employee=other_employee)
        orig_due_date = other_y.due_date

        self.complete_x_and_refresh_y(x, y)
        other_y = Task.objects.get(pk=other_y.pk)
        assert orig_due_date == other_y.due_date


class TaskRecomputeDueDateTests:
    @pytest.fixture
    def setup(self):
        responsibility = f.ResponsibilityFactory()
        task_type = f.TaskTypeFactory(
            required_within=0,
            validity_period="1 day",
            is_one_off=False,
            required_for=[responsibility],
        )
        employee = f.EmployeeFactory(
            date_of_hire=date(2015, 1, 1), other_responsibilities=[responsibility]
        )
        self.task = Task.objects.create(employee=employee, type=task_type)

    def test_recompute_saves_the_task(self, setup):
        task = self.task
        with patch.object(Task, "save") as mock:
            task.recompute_due_date()
            self.assertTrue(mock.called)

    def test_recompute_never_completed(self, setup):
        self.task.recompute_due_date()
        self.assertEqual(date(2015, 1, 1), self.task.due_date)

    def test_recompute_has_previous_completions(self, setup):
        self.task.complete(date(2015, 1, 2))
        orig_due_date = self.task.due_date
        self.task.due_date = None
        self.task.recompute_due_date()
        self.assertEqual(orig_due_date, self.task.due_date)

    def test_recompute_never_completed_with_superseding_completed(self, setup):
        superseding = f.TaskFactory(
            employee=self.task.employee,
            type__validity_period="3 days",
            type__is_one_off=False,
            type__supersedes=[self.task.type],
        )
        superseding.complete(date(2015, 3, 3))
        self.task.recompute_due_date()
        self.assertEqual(date(2015, 3, 6), self.task.due_date)

    def test_recompute_previous_completion_is_one_off(self, setup):
        """Deletes the task if previous completion is one off."""
        employee = f.EmployeeFactory()
        task_type = f.TaskTypeFactory(is_one_off=True)
        task = f.TaskFactory(employee=employee, type=task_type)
        task.complete(date(2014, 1, 1))

        task = f.TaskFactory(employee=employee, type=task_type)
        task.recompute_due_date()

        self.assertFalse(Task.objects.filter(employee=employee).exists())

    def test_recompute_previous_completion_is_one_off_plus_another(self, setup):
        """
        Make sure if one completions is one off, and another is not one
        off, the task is still deleted.
        """
        employee = f.EmployeeFactory()
        repeat = f.TaskTypeFactory(is_one_off=False)
        one_off = f.TaskTypeFactory(is_one_off=True, supersedes=[repeat])
        task = f.TaskFactory(type=repeat, employee=employee)

        # Make date after the other one so it appears first based solely
        # on expiration date.
        task.complete(date(2014, 1, 5))

        task = f.TaskFactory(type=one_off, employee=employee)
        task.complete(date(2014, 1, 1))
        task = f.TaskFactory(type=repeat, employee=employee)
        task.recompute_due_date()

        self.assertFalse(Task.objects.filter(employee=employee).exists())

    def test_recompute_required_after_not_completed(self, setup):
        """The due date should be None because the required task isnt done yet."""
        responsibility = f.ResponsibilityFactory()
        required_after_task_type = f.TaskTypeFactory(required_for=[responsibility])
        task_type = f.TaskTypeFactory(
            required_within="10 days",
            required_after=required_after_task_type,
            validity_period="1 day",
            is_one_off=False,
            required_for=[responsibility],
        )
        employee = f.EmployeeFactory(
            date_of_hire=date(2015, 1, 1), other_responsibilities=[responsibility]
        )

        task = Task.objects.create(employee=employee, type=task_type)
        task.recompute_due_date()
        self.assertIsNone(task.due_date)

    def test_recompute_required_after_completed(self):
        """The due date should be the completion date of the required_after
        task type + required_within
        """
        responsibility = f.ResponsibilityFactory()
        required_after_task_type = f.TaskTypeFactory(required_for=[responsibility])
        task_type = f.TaskTypeFactory(
            required_within="10 days",
            required_after=required_after_task_type,
            validity_period="1 day",
            is_one_off=False,
            required_for=[responsibility],
        )
        employee = f.EmployeeFactory(
            date_of_hire=date(2015, 1, 1), other_responsibilities=[responsibility]
        )

        task = Task.objects.create(employee=employee, type=task_type)
        required_task = f.TaskFactory(employee=task.employee, type=required_after_task_type)
        required_task.complete(date(2016, 1, 1))
        task.recompute_due_date()
        self.assertEqual(task.due_date, date(2016, 1, 11))

    def test_recompute_check_capacity_doesnt_pass(self):
        pass


class TaskHistoryDeleteTests(TestCase):
    """When deleting task histories it needs to update the related Task."""

    def test_updates_related_repeat_task(self):
        task = f.TaskFactory(type__is_one_off=False)
        history = task.complete(date(2015, 1, 1))

        with patch.object(Task, "recompute_due_date") as mock:
            history.delete()
            self.assertTrue(mock.called)

    def test_recreates_related_one_off_task(self):
        responsibility = f.ResponsibilityFactory()
        task_type = f.TaskTypeFactory(required_for=[responsibility], is_one_off=True)
        employee = f.EmployeeFactory(other_responsibilities=[responsibility])
        task = Task.objects.create(employee=employee, type=task_type)
        history = task.complete(date(2015, 1, 1))
        history.delete()
        self.assertTrue(Task.objects.filter(employee=task.employee, type=task.type).exists())

    def test_updates_superseded_repeat_tasks(self):
        task = f.TaskFactory(type__is_one_off=False)
        superseder = f.TaskFactory(employee=task.employee, type__supersedes=[task.type])
        history = superseder.complete(date(2015, 1, 1))

        with patch.object(Task, "recompute_due_date") as mock:
            history.delete()
            self.assertEqual(2, mock.call_count)

    def test_recreates_superseded_one_off_tasks(self):
        responsibility = f.ResponsibilityFactory()
        task_type = f.TaskTypeFactory(required_for=[responsibility], is_one_off=True)
        superseder_task_type = f.TaskTypeFactory(
            required_for=[responsibility], is_one_off=True, supersedes=[task_type]
        )
        employee = f.EmployeeFactory(other_responsibilities=[responsibility])

        task = Task.objects.create(employee=employee, type=task_type)
        superseder = Task.objects.create(employee=employee, type=superseder_task_type)
        history = superseder.complete(date(2015, 1, 1))
        history.delete()
        self.assertEqual(2, len(Task.objects.filter(employee=task.employee)))

    def test_updates_required_after_self_tasks(self):
        responsibility = f.ResponsibilityFactory()
        required_after_task_type = f.TaskTypeFactory(required_for=[responsibility], is_one_off=True)
        task_type = f.TaskTypeFactory(
            required_for=[responsibility],
            is_one_off=False,
            required_after_task_type=required_after_task_type,
        )
        employee = f.EmployeeFactory(other_responsibilities=[responsibility])

        Task.objects.create(employee=employee, type=task_type)
        required_after = Task.objects.create(employee=employee, type=required_after_task_type)
        history = required_after.complete(date(2015, 1, 1))

        with patch.object(Task, "recompute_due_date") as mock:
            history.delete()
            self.assertEqual(2, mock.call_count)


class FacilityQuestionTest(TestCase):
    def test_facility_question_must_have_question(self):
        self.assertTrue(hasattr(f.FacilityQuestionFactory(), "question"))

    def test_user_should_be_able_to_mark_a_question_as_license(self):
        self.assertTrue(hasattr(f.FacilityQuestionFactory(), "is_license"))

    def test_facility_question_must_have_a_description(self):
        self.assertTrue(hasattr(f.FacilityQuestionFactory(), "description"))

    def test_facility_question_can_belong_to_many_facilities(self):
        question = f.FacilityQuestionFactory()
        facility1 = f.FacilityFactory()
        facility2 = f.FacilityFactory()
        facility1.questions.add(question)
        facility2.questions.add(question)

        self.assertIn(question, facility1.questions.all())
        self.assertIn(question, facility2.questions.all())

    def test_facility_question_can_have_rules(self):
        question = f.FacilityQuestionFactory()
        rule1 = f.FacilityQuestionRuleFactory()
        rule2 = f.FacilityQuestionRuleFactory()
        question.rules.add(rule1)
        question.rules.add(rule2)

        self.assertIn(rule1, question.rules.all())
        self.assertIn(rule2, question.rules.all())


class FacilityQuestionRuleTest(TestCase):
    def setUp(self):
        self.question = f.FacilityQuestionFactory()
        self.facility = f.FacilityFactory()

        self.facility.questions.add(self.question)

        self.position = f.PositionFactory()
        self.responsibility = f.ResponsibilityFactory()

        self.rule = f.FacilityQuestionRuleFactory(
            facility_question=self.question,
            position=self.position,
            responsibility=self.responsibility,
        )

        self.question.rules.add(self.rule)
        self.employee = f.EmployeeFactory(facility=self.facility)
        self.employee.positions.add(self.position)

    def test_rules_add_responsibilities_to_positions(self):
        responsibilities = self.employee.other_responsibilities.all()
        self.assertIn(self.responsibility, responsibilities)

    def test_modifying_rule_modifies_employee_responsibilities(self):
        employee1 = f.EmployeeFactory(facility=self.facility)
        employee2 = f.EmployeeFactory(facility=self.facility)
        employee1.positions.add(self.position)
        employee2.positions.add(self.position)
        new_responsibility = f.ResponsibilityFactory()
        self.rule.responsibility = new_responsibility
        self.rule.save()
        responsibilities1 = employee1.other_responsibilities.all()
        responsibilities2 = employee2.other_responsibilities.all()

        self.assertIn(new_responsibility, responsibilities1)
        self.assertIn(new_responsibility, responsibilities2)

    def test_no_duplicate_responsibilities_added(self):
        new_responsibility = f.ResponsibilityFactory()
        self.employee.other_responsibilities.add(new_responsibility)

        f.FacilityQuestionRuleFactory(
            facility_question=self.question,
            position=self.position,
            responsibility=new_responsibility,
        )

        responsibilities = self.employee.other_responsibilities.all()
        self.assertIn(new_responsibility, responsibilities)
        self.assertEqual(2, responsibilities.count())


class AntirequisiteTest(TestCase):
    def test_old_employees_must_have_antirequisite_task(self):
        """
        If an `Antirequisite` is created, all existing employees must have the
        `Antirequisite` task in their set of tasks
        """
        responsibility = f.ResponsibilityFactory()
        task_type1 = f.TaskTypeFactory()
        task_type2 = f.TaskTypeFactory()
        task_type2.required_for.add(responsibility)

        employee = f.EmployeeFactory(date_of_hire=date(2015, 7, 4))
        employee.other_responsibilities.add(responsibility)

        f.AntirequisiteFactory(
            task_type=task_type1,
            antirequisite_of=task_type2,
            valid_after_hire_date=date(2015, 7, 4),
        )

        tasks = employee.trainings_task_set.all()
        task1 = employee.trainings_task_set.get(type=task_type1)
        task2 = employee.trainings_task_set.get(type=task_type2)

        self.assertIsInstance(task1.antirequisite, Antirequisite)
        self.assertIn(task1, tasks)
        self.assertIn(task2, tasks)

    def test_new_employees_must_have_antirequisite_task(self):
        """
        If an `Antirequisite` exists, new employees must have the
        `Antirequisite` task in their set of tasks
        """
        responsibility = f.ResponsibilityFactory()
        task_type1 = f.TaskTypeFactory()
        task_type2 = f.TaskTypeFactory()
        task_type2.required_for.add(responsibility)

        f.AntirequisiteFactory(
            task_type=task_type1,
            antirequisite_of=task_type2,
            valid_after_hire_date=date(2015, 7, 4),
        )

        new_employee = f.EmployeeFactory(date_of_hire=date(2015, 7, 4))
        new_employee.other_responsibilities.add(responsibility)

        tasks = new_employee.trainings_task_set.all()
        task1 = new_employee.trainings_task_set.get(type=task_type1)
        task2 = new_employee.trainings_task_set.get(type=task_type2)

        self.assertIsInstance(task1.antirequisite, Antirequisite)
        self.assertIn(task1, tasks)
        self.assertIn(task2, tasks)

    def test_antirequisite_one_off_task_is_not_created_if_done(self):
        """
        No one-off antirequisite task should be added to the employee's
        outstanding tasks/trainings if the employee is already finished
        with the task
        """
        responsibility = f.ResponsibilityFactory()
        task_type1 = f.TaskTypeFactory(is_one_off=True)
        task_type2 = f.TaskTypeFactory()
        task_type2.required_for.add(responsibility)

        f.AntirequisiteFactory(
            task_type=task_type1,
            antirequisite_of=task_type2,
            valid_after_hire_date=date(2015, 7, 4),
        )

        new_employee = f.EmployeeFactory(date_of_hire=date(2015, 7, 4))
        new_employee.other_responsibilities.add(responsibility)
        task1 = new_employee.trainings_task_set.filter(type=task_type1).first()
        task1.complete(date(2015, 7, 4))
        new_employee.other_responsibilities.remove(responsibility)
        new_employee.other_responsibilities.add(responsibility)
        task1 = new_employee.trainings_task_set.filter(type=task_type1).first()
        self.assertIsNone(task1)

    def test_employees_must_have_task_updated_if_antirequisite(self):
        """
        If an `Antirequisite` is created, all existing employees that already
        have the antirequisite task in their set of tasks must have that
        task's due date updated
        """
        responsibility = f.ResponsibilityFactory()
        task_type1 = f.TaskTypeFactory()
        task_type1.required_for.add(responsibility)
        task_type2 = f.TaskTypeFactory()
        task_type2.required_for.add(responsibility)

        date_of_hire = date(2015, 7, 5)
        employee = f.EmployeeFactory(date_of_hire=date_of_hire)
        employee.other_responsibilities.add(responsibility)

        f.AntirequisiteFactory(
            task_type=task_type1,
            antirequisite_of=task_type2,
            valid_after_hire_date=date(2015, 7, 4),
        )

        tasks = employee.trainings_task_set.all()
        task1 = employee.trainings_task_set.get(type=task_type1)
        task2 = employee.trainings_task_set.get(type=task_type2)

        self.assertEqual(task1.due_date, date_of_hire)
        self.assertIn(task1, tasks)
        self.assertIn(task2, tasks)

    def test_employees_must_have_task_removed_if_antirequisite_is_deleted(self):
        """
        If an `Antirequisite` is deleted, all employees that have the
        antirequisite task in their set of tasks must no longer
        have it
        """
        responsibility = f.ResponsibilityFactory()
        task_type1 = f.TaskTypeFactory()
        task_type2 = f.TaskTypeFactory()
        task_type2.required_for.add(responsibility)

        date_of_hire = date(2015, 7, 5)
        employee = f.EmployeeFactory(date_of_hire=date_of_hire)
        employee.other_responsibilities.add(responsibility)

        antirequisite = f.AntirequisiteFactory(
            task_type=task_type1,
            antirequisite_of=task_type2,
            valid_after_hire_date=date(2015, 7, 4),
        )

        tasks = employee.trainings_task_set.all()
        task1 = employee.trainings_task_set.get(type=task_type1)
        task2 = employee.trainings_task_set.get(type=task_type2)

        self.assertIn(task1, tasks)

        antirequisite.delete()
        tasks = employee.trainings_task_set.all()

        self.assertNotIn(task1, tasks)
        self.assertIn(task2, tasks)

    def test_task_type_is_not_required_if_employee_is_hired_after_valid_date_and_antirequisite_is_completed_before_date_of_hire(
        self,
    ):
        responsibility = f.ResponsibilityFactory()
        task_type = f.TaskTypeFactory()
        antirequisite_type = f.TaskTypeFactory(validity_period="5 days")
        antirequisite_type.required_for.add(responsibility)

        f.AntirequisiteFactory(
            task_type=task_type,
            antirequisite_of=antirequisite_type,
            valid_after_hire_date=date(2015, 7, 4),
        )

        employee = f.EmployeeFactory(date_of_hire=date(2015, 7, 4))
        employee.other_responsibilities.add(responsibility)

        task = employee.trainings_task_set.get(type=task_type)
        assert task.due_date == date(2015, 7, 4)

        antirequisite_task = employee.trainings_task_set.get(type=antirequisite_type)
        antirequisite_task.complete(date(2015, 7, 3))
        task.refresh_from_db()
        assert task.due_date == date(2015, 7, 8)

    def test_task_type_is_required_if_employee_is_hired_after_valid_date_and_antirequisite_is_completed_after_date_of_hire(
        self,
    ):
        responsibility = f.ResponsibilityFactory()
        task_type = f.TaskTypeFactory()
        antirequisite_type = f.TaskTypeFactory(validity_period="5 days")
        antirequisite_type.required_for.add(responsibility)

        f.AntirequisiteFactory(
            task_type=task_type,
            antirequisite_of=antirequisite_type,
            valid_after_hire_date=date(2015, 7, 4),
        )

        employee = f.EmployeeFactory(date_of_hire=date(2015, 7, 4))
        employee.other_responsibilities.add(responsibility)

        task = employee.trainings_task_set.get(type=task_type)
        assert task.due_date == date(2015, 7, 4)

        antirequisite_task = employee.trainings_task_set.get(type=antirequisite_type)
        antirequisite_task.complete(date(2015, 7, 5))
        task.refresh_from_db()
        assert task.due_date == date(2015, 7, 4)


class FacilityTest(TestCase):
    def test_facility_has_default(self):
        facility = f.FacilityFactory()
        self.assertIsInstance(facility.default, FacilityDefault)

    def test_facility_only_has_the_original_default(self):
        facility = f.FacilityFactory()
        default_id = facility.default.pk
        facility.save()
        facility = Facility.objects.get(pk=facility.pk)
        self.assertEqual(default_id, facility.default.pk)

    def test_facility_without_capacity_dont_add_employee_requirements(self):
        facility = f.FacilityFactory()
        task_type = f.TaskTypeFactory(facility=facility, min_capacity=3, max_capacity=5)
        employee = f.EmployeeFactory(facility=facility)
        f.TaskFactory(employee=employee, type=task_type)

        facility.capacity = 0
        facility.save()
        assert employee.trainings_task_set.count() == 0

    def test_update_capacity_add_employee_requirements(self):
        facility = f.FacilityFactory()
        responsibility = f.ResponsibilityFactory()
        task_type = f.TaskTypeFactory(
            facility=facility,
            required_for=[responsibility],
            min_capacity=3,
            max_capacity=5,
        )
        task_type_2 = f.TaskTypeFactory(
            required_for=[responsibility], min_capacity=3, max_capacity=5
        )
        employee = f.EmployeeFactory(facility=facility, other_responsibilities=[responsibility])

        for valid_capacity in range(3, 6):
            facility.capacity = valid_capacity
            facility.save()
            ids = employee.trainings_task_set.all().values_list("type_id")
            assert len(ids) == 2
            assert (task_type.id,) in ids
            assert (task_type_2.id,) in ids


class TestGlobalRequirement:
    def test_employee_task_is_created_when_requirement_is_created(self):
        f.EmployeeFactory()
        f.GlobalRequirementFactory()
        assert Task.objects.count() == 1

    def test_employee_task_is_deleted_when_requirement_is_deleted(self):
        f.EmployeeFactory()
        global_requirement = f.GlobalRequirementFactory()
        global_requirement.delete()
        assert Task.objects.count() == 0

    def test_new_employee_is_required_to_take_task_type(self):
        f.GlobalRequirementFactory()
        f.EmployeeFactory()
        assert Task.objects.count() == 1


class TestPosition:
    def test_requirements_are_updated_when_position_changes(self):
        position = f.PositionFactory()
        f.EmployeeFactory(positions=[position])
        assert Task.objects.count() == 0

        responsibility = f.ResponsibilityFactory()
        f.TaskTypeFactory(required_for=[responsibility])
        position.responsibilities.add(responsibility)
        assert Task.objects.count() == 1

    def test_responsibility_with_position_restriction_is_removed_when_position_is_removed(
        self,
    ):
        cna = f.PositionFactory(name="Nursing Assistant")
        reminder = f.ResponsibilityFactory(
            question="want reminders?", question_position_restriction=cna
        )
        bob = f.EmployeeFactory(positions=[cna])
        bob.other_responsibilities.add(reminder)  # say yes to the question
        bob.positions.remove(cna)
        assert bob.other_responsibilities.count() == 0


class TestFacilityQuestionsChanged:
    def test_adds_responsibility_to_employee_with_position_when_question_added(self):
        facility = f.FacilityFactory()
        nurse = f.PositionFactory()
        get_good = f.ResponsibilityFactory()
        employee = f.EmployeeFactory(positions=[nurse])

        question_rule = f.FacilityQuestionRuleFactory(position=nurse, responsibility=get_good)
        facility.questions.add(question_rule.facility_question)
        assert employee.other_responsibilities.count() == 1

    def test_doesnt_add_responsibility_to_employee_without_position_when_question_added(
        self,
    ):
        facility = f.FacilityFactory()
        nurse = f.PositionFactory()
        get_good = f.ResponsibilityFactory()
        employee = f.EmployeeFactory()

        question_rule = f.FacilityQuestionRuleFactory(position=nurse, responsibility=get_good)
        facility.questions.add(question_rule.facility_question)
        assert employee.other_responsibilities.count() == 0

    def test_removes_responsibility_from_employee_with_position_when_question_removed(
        self,
    ):
        facility = f.FacilityFactory()
        nurse = f.PositionFactory()
        get_good = f.ResponsibilityFactory()
        employee = f.EmployeeFactory(positions=[nurse])

        question_rule = f.FacilityQuestionRuleFactory(position=nurse, responsibility=get_good)
        facility.questions.add(question_rule.facility_question)
        facility.questions.remove(question_rule.facility_question)
        assert employee.other_responsibilities.count() == 0
