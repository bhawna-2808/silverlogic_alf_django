import datetime

from django.test import TestCase
from django.utils import timezone

import pytest
import pytz
from constance.test import override_config
from dateutil.relativedelta import relativedelta
from mock import patch

from apps.facilities.models import FacilityUser
from apps.trainings.tasks import (
    EmailCompletedTrainingsReminderToday,
    EmailEmployeeEvents,
    EmailFacilityCompliant,
    EmailOverdueTasksThisWeek,
    EmailScheduledTrainingsToday,
    ResetPrerequisiteTasks,
    SMSInPersonTrainingReminders,
    SMSPastDueReminders,
    SMSUpcomingReminders,
    email_birthday_reminder,
    email_monthly_reminders,
    get_emails,
)

import tests.factories as f

pytestmark = pytest.mark.django_db


class GetAdminEmailsTest(TestCase):
    def test_returns_a_list_of_emails(self):
        employee1 = f.EmployeeFactory(receives_emails=True, email="test1@test.com")
        employee2 = f.EmployeeFactory(receives_emails=True, email="test2@test.com")
        emails = get_emails(employee1.facility)
        self.assertIn(employee1.email, emails)
        self.assertIn(employee2.email, emails)

    def test_does_not_get_email_just_because_of_admin(self):
        """This was old functionality"""
        admin_position = f.PositionFactory(name="Administrator")
        admin = f.EmployeeFactory(receives_emails=False)
        admin.positions.add(admin_position)
        self.assertEqual(0, len(get_emails(admin.facility)))

    def test_does_not_get_empty_emails(self):
        employee = f.EmployeeFactory(receives_emails=True, email="")
        self.assertEqual(0, len(get_emails(employee.facility)))

    def test_does_not_get_null_emails(self):
        employee = f.EmployeeFactory(receives_emails=True, email=None)
        self.assertEqual(0, len(get_emails(employee.facility)))

    def test_does_not_get_email_from_other_facility(self):
        facility = f.FacilityFactory(name="my facility")
        employee = f.EmployeeFactory(receives_emails=True, facility__name="not my facility")

        self.assertEqual(0, len(get_emails(facility)))
        self.assertEqual(1, len(get_emails(employee.facility)))

    def test_inactive_employees_are_not_included(self):
        employee = f.EmployeeFactory(receives_emails=True, is_active=False)
        self.assertEqual(0, len(get_emails(employee.facility)))


class TestEmailEmployeeEvents:
    def test_email_is_sent_to_attendees(self, outbox):
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        employee1 = f.EmployeeFactory(email="employee1@fake.com", receives_emails=True)
        employee2 = f.EmployeeFactory(email="employee2@fake.com", receives_emails=True)
        f.TrainingEventFactory(start_time=tomorrow, attendees=[employee1])
        f.TrainingEventFactory(start_time=tomorrow, attendees=[employee2])
        emailer = EmailEmployeeEvents()
        emailer.do()

        assert outbox[0].to[0] == employee1.email
        assert outbox[1].to[0] == employee2.email
        assert len(outbox) == 2

    def test_email_contains_correct_date(self, outbox):
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        in_three_days = timezone.now() + datetime.timedelta(days=3)
        employee1 = f.EmployeeFactory(email="employee1@fake.com", receives_emails=True)
        training_event_1 = f.TrainingEventFactory(start_time=tomorrow, attendees=[employee1])
        training_event_2 = f.TrainingEventFactory(start_time=in_three_days, attendees=[employee1])
        training_event_3 = f.TrainingEventFactory(start_time=in_three_days, attendees=[employee1])

        emailer = EmailEmployeeEvents()
        emailer.do()

        assert training_event_1.training_for.name in outbox[0].body
        assert training_event_2.training_for.name in outbox[1].body
        assert training_event_3.training_for.name in outbox[1].body

    def test_email_contains_correct_subject(self, outbox):
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        employee1 = f.EmployeeFactory(email="employee1@fake.com", receives_emails=True)
        f.TrainingEventFactory(start_time=tomorrow, attendees=[employee1])

        emailer = EmailEmployeeEvents()
        emailer.do()

        assert "You are enrolled for training" in outbox[0].subject

    def test_does_not_send_mail_when_no_events(self, outbox):
        f.EmployeeFactory(email="employee1@fake.com", receives_emails=True)

        emailer = EmailEmployeeEvents()
        emailer.do()

        assert len(outbox) == 0


class EmailScheduledTrainingsTodayTest(TestCase):
    @patch("apps.trainings.tasks.send_mail")
    def test_emails_are_sent_for_trainings_today(self, send_mail_mock):
        now = timezone.now()
        facility1 = f.FacilityFactory(name="Facility1")
        facility2 = f.FacilityFactory(name="Facility2")
        f.TrainingEventFactory(start_time=now, facility=facility1)
        f.TrainingEventFactory(start_time=now, facility=facility2)
        employee1 = f.EmployeeFactory(
            facility=facility1, email="admin1@fake.com", receives_emails=True
        )
        f.FacilityUserFactory(user=employee1.user, role=FacilityUser.Role.account_admin)
        employee2 = f.EmployeeFactory(
            facility=facility2, email="admin2@fake.com", receives_emails=True
        )
        f.FacilityUserFactory(user=employee2.user, role=FacilityUser.Role.account_admin)

        emailer = EmailScheduledTrainingsToday()
        emailer.do()

        self.assertEqual(send_mail_mock.call_count, 2)

        # Asserts that the admin1's email is included in the recipient list
        self.assertIn(employee1.email, send_mail_mock.call_args_list[0][1]["recipient_list"])

        # Asserts that the admin2's email is included in the recipient list
        self.assertIn(employee2.email, send_mail_mock.call_args_list[1][1]["recipient_list"])

    @patch("apps.trainings.tasks.send_mail")
    def test_no_emails_are_sent_for_zero_trainings_today(self, send_mail_mock):
        facility1 = f.FacilityFactory(name="Facility1")
        f.EmployeeFactory(facility=facility1, email="admin1@fake.com", receives_emails=True)

        emailer = EmailScheduledTrainingsToday()
        emailer.do()

        self.assertEqual(send_mail_mock.call_count, 0)

    @patch("apps.trainings.tasks.send_mail")
    def test_emails_are_sent_for_administrators_only(self, send_mail_mock):
        now = timezone.now()
        facility = f.FacilityFactory(name="Facility")
        f.TrainingEventFactory(start_time=now, facility=facility)

        employee_admin = f.EmployeeFactory(
            facility=facility, email="admin@fake.com", receives_emails=True
        )
        f.FacilityUserFactory(user=employee_admin.user, role=FacilityUser.Role.account_admin)
        employee_manager = f.EmployeeFactory(
            facility=facility, email="manager@fake.com", receives_emails=True
        )
        f.FacilityUserFactory(user=employee_manager.user, role=FacilityUser.Role.account_admin)
        employee_examiner = f.EmployeeFactory(
            facility=facility, email="examiner@fake.com", receives_emails=True
        )
        f.FacilityUserFactory(user=employee_examiner.user, role=FacilityUser.Role.trainings_user)
        employee_trainings_user = f.EmployeeFactory(
            facility=facility, email="trainings_user@fake.com", receives_emails=True
        )
        f.FacilityUserFactory(
            user=employee_trainings_user.user, role=FacilityUser.Role.trainings_user
        )

        emailer = EmailScheduledTrainingsToday()
        emailer.do()

        all_recipients = list(send_mail_mock.call_args_list[0][1]["recipient_list"])
        self.assertIn(employee_admin.email, all_recipients)
        self.assertIn(employee_manager.email, all_recipients)
        self.assertNotIn(employee_examiner.email, all_recipients)
        self.assertNotIn(employee_trainings_user.email, all_recipients)


class EmailOverdueTasksThisWeekTest(TestCase):
    @patch("apps.trainings.tasks.send_mail")
    def test_emails_are_sent_for_overdue_tasks_on_monday(self, send_mail_mock):
        employee = f.EmployeeFactory(email="test@test.com", receives_emails=True)
        f.FacilityUserFactory(user=employee.user, role=FacilityUser.Role.account_admin)
        f.TaskFactory(overdue=True)

        with patch("apps.trainings.tasks.timezone.now") as mock:
            # monday
            mock.return_value = datetime.datetime(2016, 5, 23, tzinfo=pytz.UTC)
            emailer = EmailOverdueTasksThisWeek()
            emailer.do()

        self.assertEqual(send_mail_mock.call_count, 1)

        # Asserts that the email is included in the recipient list
        self.assertIn(employee.email, send_mail_mock.call_args[1]["recipient_list"])

    @patch("apps.trainings.tasks.send_mail")
    def test_emails_are_not_sent_for_overdue_tasks_on_non_monday(self, send_mail_mock):
        employee = f.EmployeeFactory(email="test@test.com", receives_emails=True)
        f.FacilityUserFactory(user=employee.user, role=FacilityUser.Role.account_admin)
        f.TaskFactory(overdue=True)

        with patch("apps.trainings.tasks.timezone.now") as mock:
            # not monday
            mock.return_value = datetime.datetime(2016, 5, 24, tzinfo=pytz.UTC)
            emailer = EmailOverdueTasksThisWeek()
            emailer.do()

        self.assertEqual(send_mail_mock.call_count, 0)

    @patch("apps.trainings.tasks.send_mail")
    def test_emails_are_sent_for_administrators_only(self, send_mail_mock):
        employee = f.EmployeeFactory(email="test@test.com", receives_emails=True)
        facility = employee.facility
        # employees who have no user associated but are still administrators should receive admin emails
        employee_admin_no_user = f.EmployeeFactory(
            facility=facility,
            email="adminnouser@fake.com",
            receives_emails=True,
            user=None,
        )
        position_admin = f.PositionFactory(name="Administrator")
        employee_manager_no_user = f.EmployeeFactory(
            facility=facility,
            email="mannouser@fake.com",
            receives_emails=True,
            user=None,
        )
        position_manager = f.PositionFactory(name="Manager")
        employee_manager_no_user.positions.add(position_manager)
        employee_admin_no_user.positions.add(position_admin)
        employee_admin = f.EmployeeFactory(
            facility=facility, email="admin@fake.com", receives_emails=True
        )
        f.FacilityUserFactory(user=employee_admin.user, role=FacilityUser.Role.account_admin)
        employee_manager = f.EmployeeFactory(
            facility=facility, email="manager@fake.com", receives_emails=True
        )
        f.FacilityUserFactory(user=employee_manager.user, role=FacilityUser.Role.account_admin)
        # examiner role should not be included in the list of admin emails
        employee_examiner_no_user = f.EmployeeFactory(
            facility=facility,
            email="examinernouser@fake.com",
            receives_emails=True,
            user=None,
        )
        position_examiner = f.PositionFactory(name="Med Tech")
        employee_examiner_no_user.positions.add(position_examiner)
        employee_examiner = f.EmployeeFactory(
            facility=facility, email="examiner@fake.com", receives_emails=True
        )
        f.FacilityUserFactory(user=employee_examiner.user, role=FacilityUser.Role.trainings_user)
        employee_trainings_user = f.EmployeeFactory(
            facility=facility, email="trainings_user@fake.com", receives_emails=True
        )
        f.FacilityUserFactory(
            user=employee_trainings_user.user, role=FacilityUser.Role.trainings_user
        )

        f.TaskFactory(overdue=True)

        with patch("apps.trainings.tasks.timezone.now") as mock:
            # monday
            mock.return_value = datetime.datetime(2016, 5, 23, tzinfo=pytz.UTC)
            emailer = EmailOverdueTasksThisWeek()
            emailer.do()

        with patch("apps.trainings.tasks.timezone.now") as mock:
            # monday
            mock.return_value = datetime.datetime(2016, 5, 23, tzinfo=pytz.UTC)
            emailer = EmailOverdueTasksThisWeek()
            emailer.do()

        all_recipients = list(send_mail_mock.call_args_list[0][1]["recipient_list"])
        self.assertIn(employee_manager_no_user.email, all_recipients)
        assert all_recipients.count(employee_manager_no_user.email) == 1
        self.assertIn(employee_admin_no_user.email, all_recipients)
        self.assertIn(employee_admin.email, all_recipients)
        self.assertIn(employee_manager.email, all_recipients)
        self.assertNotIn(employee_examiner.email, all_recipients)
        self.assertNotIn(employee_examiner_no_user.email, all_recipients)
        self.assertNotIn(employee_trainings_user.email, all_recipients)


class EmailFacilityCompliantTest(TestCase):
    @patch("apps.trainings.tasks.send_mail")
    def test_emails_are_sent_for_facility_compliance(self, send_mail_mock):
        employee = f.EmployeeFactory(email="test@test.com", receives_emails=True)

        with patch("apps.trainings.tasks.timezone.now") as mock:
            # monday
            mock.return_value = datetime.datetime(2016, 5, 23, tzinfo=pytz.UTC)
            emailer = EmailFacilityCompliant()
            emailer.do()

        self.assertEqual(send_mail_mock.call_count, 1)

        # Asserts that the admin's email is included in the recipient list
        self.assertIn(employee.email, send_mail_mock.call_args[1]["recipient_list"])

    @patch("apps.trainings.tasks.send_mail")
    def test_emails_are_not_sent_for_facility_non_compliance(self, send_mail_mock):
        f.TaskFactory(overdue=True)  # make facility non compliant
        f.EmployeeFactory(email="test@test.com", receives_emails=True)

        with patch("apps.trainings.tasks.timezone.now") as mock:
            # monday
            mock.return_value = datetime.datetime(2016, 5, 24, tzinfo=pytz.UTC)
            emailer = EmailFacilityCompliant()
            emailer.do()

        self.assertEqual(send_mail_mock.call_count, 0)

    @patch.object(EmailFacilityCompliant, "mail_facility_compliance")
    def test_ninety_day_task_type_is_included(self, mail_facility_compliance_mock):
        employee = f.EmployeeFactory()
        task = f.TaskFactory(
            due_date=timezone.now().date() + datetime.timedelta(days=89),
            employee=employee,
            type=f.TaskTypeFactory(),
        )
        f.EmployeeFactory(email="admin@fake.com", receives_emails=True)

        with patch("apps.trainings.tasks.timezone.now") as mock:
            # monday
            mock.return_value = datetime.datetime(2016, 5, 23, tzinfo=pytz.UTC)
            emailer = EmailFacilityCompliant()
            emailer.do()

        self.assertEqual(mail_facility_compliance_mock.call_count, 1)

        ninety_day_task_types = mail_facility_compliance_mock.call_args[0][0]

        # Asserts that the task type is included in the task type list for the
        # first argument of the method.
        self.assertIn(task.type, ninety_day_task_types)

    @patch("apps.trainings.tasks.send_mail")
    def test_only_runs_on_mondays(self, send_mail_mock):
        f.EmployeeFactory(email="admin@fake.com", receives_emails=True)

        with patch("apps.trainings.tasks.timezone.now") as mock:
            # not monday
            mock.return_value = datetime.datetime(2016, 5, 24, tzinfo=pytz.UTC)
            emailer = EmailFacilityCompliant()
            emailer.do()

        self.assertEqual(send_mail_mock.call_count, 0)


class EmailCompletedTrainingsReminderTest(TestCase):
    @patch("apps.trainings.tasks.send_mail")
    def test_emails_are_sent_for_trainings_today(self, send_mail_mock):
        yesterday = timezone.now() - datetime.timedelta(days=1)
        facility1 = f.FacilityFactory(name="Facility1")
        facility2 = f.FacilityFactory(name="Facility2")
        f.TrainingEventFactory(end_time=yesterday, facility=facility1)
        f.TrainingEventFactory(end_time=yesterday, facility=facility2)
        employee1 = f.EmployeeFactory(
            facility=facility1, email="admin1@fake.com", receives_emails=True
        )
        f.FacilityUserFactory(user=employee1.user, role=FacilityUser.Role.account_admin)
        employee2 = f.EmployeeFactory(
            facility=facility2, email="admin2@fake.com", receives_emails=True
        )
        f.FacilityUserFactory(user=employee2.user, role=FacilityUser.Role.account_admin)

        emailer = EmailCompletedTrainingsReminderToday()
        emailer.do()

        self.assertEqual(send_mail_mock.call_count, 2)

        # Asserts that the employee1's email is included in the recipient list
        all_recipients = list(send_mail_mock.call_args_list[0][1]["recipient_list"]) + list(
            send_mail_mock.call_args_list[1][1]["recipient_list"]
        )

        self.assertIn(employee1.email, all_recipients)

        # Asserts that the employee2's email is included in the recipient list
        self.assertIn(employee2.email, all_recipients)

    @patch("apps.trainings.tasks.send_mail")
    def test_emails_are_sent_for_administrators_only(self, send_mail_mock):
        yesterday = timezone.now() - datetime.timedelta(days=1)
        facility = f.FacilityFactory(name="Facility")
        f.TrainingEventFactory(end_time=yesterday, facility=facility)

        employee_admin = f.EmployeeFactory(
            facility=facility, email="admin@fake.com", receives_emails=True
        )
        f.FacilityUserFactory(user=employee_admin.user, role=FacilityUser.Role.account_admin)
        employee_manager = f.EmployeeFactory(
            facility=facility, email="manager@fake.com", receives_emails=True
        )
        f.FacilityUserFactory(user=employee_manager.user, role=FacilityUser.Role.account_admin)
        employee_examiner = f.EmployeeFactory(
            facility=facility, email="examiner@fake.com", receives_emails=True
        )
        f.FacilityUserFactory(user=employee_examiner.user, role=FacilityUser.Role.trainings_user)
        employee_trainings_user = f.EmployeeFactory(
            facility=facility, email="trainings_user@fake.com", receives_emails=True
        )
        f.FacilityUserFactory(
            user=employee_trainings_user.user, role=FacilityUser.Role.trainings_user
        )

        emailer = EmailCompletedTrainingsReminderToday()
        emailer.do()

        all_recipients = list(send_mail_mock.call_args_list[0][1]["recipient_list"])
        self.assertIn(employee_admin.email, all_recipients)
        self.assertIn(employee_manager.email, all_recipients)
        self.assertNotIn(employee_examiner.email, all_recipients)
        self.assertNotIn(employee_trainings_user.email, all_recipients)


class ResetPrerequisiteTaskTest(TestCase):
    def setUp(self):
        self.reset = ResetPrerequisiteTasks()

    def test_reset_prerequisite_tasks(self):
        facility = f.FacilityFactory()
        employee = f.EmployeeFactory(facility=facility)
        position = f.PositionFactory()
        responsibility = f.ResponsibilityFactory()
        position.responsibilities.add(responsibility)
        employee.positions.add(position)
        task_type1 = f.TaskTypeFactory(validity_period=datetime.timedelta(days=60))
        task_type1.required_for.add(responsibility)
        task_type2 = f.TaskTypeFactory(validity_period=datetime.timedelta(days=60))
        task_type2.required_for.add(responsibility)
        task_type2.prerequisites.add(task_type1)
        completion_date = datetime.date(2015, 1, 31)
        task1 = f.TaskFactory(employee=employee, type=task_type1)
        task1.complete(completion_date)
        self.assertEqual(task1.due_date, completion_date + task1.type.validity_period)
        task2 = f.TaskFactory(employee=employee, type=task_type2)
        task2.complete(completion_date)
        self.assertEqual(task2.due_date, completion_date + task2.type.validity_period)

        requirement = f.ResponsibilityEducationRequirementFactory(
            responsibility=responsibility,
            interval_base=task_type2,
            timeperiod=datetime.timedelta(days=30),
            start_over=True,
        )

        reset = ResetPrerequisiteTasks()
        reset.now_date = datetime.date(2015, 12, 31)
        reset.do()

        task2 = employee.trainings_task_set.get(pk=task2.pk)
        task1 = employee.trainings_task_set.get(pk=task1.pk)
        self.assertEqual(task2.due_date, completion_date + requirement.timeperiod)
        self.assertEqual(task1.due_date, completion_date + requirement.timeperiod)

    def test_circular_prerequisites_will_not_cause_recursion_error(self):
        facility = f.FacilityFactory()
        employee = f.EmployeeFactory(facility=facility)
        position = f.PositionFactory()
        responsibility = f.ResponsibilityFactory()
        position.responsibilities.add(responsibility)
        employee.positions.add(position)

        task_type1 = f.TaskTypeFactory(validity_period=datetime.timedelta(days=60))
        task_type1.required_for.add(responsibility)
        task_type2 = f.TaskTypeFactory(validity_period=datetime.timedelta(days=60))
        task_type2.required_for.add(responsibility)
        task_type2.prerequisites.add(task_type1)
        task_type3 = f.TaskTypeFactory(validity_period=datetime.timedelta(days=60))
        task_type3.required_for.add(responsibility)
        task_type3.prerequisites.add(task_type2)
        task_type1.prerequisites.add(task_type3)

        completion_date = datetime.date(2015, 1, 31)
        task1 = f.TaskFactory(employee=employee, type=task_type1)
        task1.complete(completion_date)
        task2 = f.TaskFactory(employee=employee, type=task_type2)
        task2.complete(completion_date)
        task3 = f.TaskFactory(employee=employee, type=task_type3)
        task3.complete(completion_date)

        requirement = f.ResponsibilityEducationRequirementFactory(
            responsibility=responsibility,
            interval_base=task_type3,
            timeperiod=datetime.timedelta(days=30),
            start_over=True,
        )

        reset = ResetPrerequisiteTasks()
        reset.now_date = datetime.date(2015, 12, 31)
        reset.do()

        task3 = employee.trainings_task_set.get(pk=task3.pk)
        task2 = employee.trainings_task_set.get(pk=task2.pk)
        task1 = employee.trainings_task_set.get(pk=task1.pk)

        self.assertEqual(task3.due_date, completion_date + requirement.timeperiod)
        self.assertEqual(task2.due_date, completion_date + requirement.timeperiod)
        self.assertEqual(task1.due_date, completion_date + requirement.timeperiod)

    def test_completed_prerequisite_interval_bases_are_not_reset(self):
        facility = f.FacilityFactory()
        employee = f.EmployeeFactory(facility=facility)
        position = f.PositionFactory()
        responsibility = f.ResponsibilityFactory()
        position.responsibilities.add(responsibility)
        employee.positions.add(position)
        task_type1 = f.TaskTypeFactory(validity_period=datetime.timedelta(days=60))
        task_type1.required_for.add(responsibility)
        task_type2 = f.TaskTypeFactory(validity_period=datetime.timedelta(days=60))
        task_type2.required_for.add(responsibility)
        task_type2.prerequisites.add(task_type1)
        completion_date = datetime.date(2015, 1, 31)
        task1 = f.TaskFactory(employee=employee, type=task_type1)
        task1.complete(completion_date)
        task2 = f.TaskFactory(employee=employee, type=task_type2)
        task2.complete(completion_date)

        f.ResponsibilityEducationRequirementFactory(
            responsibility=responsibility,
            interval_base=task_type2,
            timeperiod=datetime.timedelta(days=30),
            start_over=True,
            hours=10,
            type=1,
        )

        credit_task_type = f.TaskTypeFactory()
        f.TaskTypeEducationCreditFactory(type=1, tasktype=credit_task_type)
        credit_task = f.TaskFactory(employee=employee, type=credit_task_type)
        credit_task.complete(completion_date, 10)

        reset = ResetPrerequisiteTasks()
        reset.now_date = datetime.date(2015, 12, 31)
        reset.do()

        task2 = employee.trainings_task_set.get(pk=task2.pk)

        self.assertEqual(task2.due_date, completion_date + task2.type.validity_period)

    def test_get_requirements(self):
        position = f.PositionFactory()
        responsibility = f.ResponsibilityFactory()
        position.responsibilities.add(responsibility)
        task_type1 = f.TaskTypeFactory()
        task_type1.required_for.add(responsibility)
        task_type2 = f.TaskTypeFactory()
        task_type2.required_for.add(responsibility)
        task_type2.prerequisites.add(task_type1)
        task_type3 = f.TaskTypeFactory()
        task_type3.required_for.add(responsibility)
        employee = f.EmployeeFactory()
        employee.positions.add(position)

        requirement1 = f.ResponsibilityEducationRequirementFactory(
            responsibility=responsibility, interval_base=task_type2, start_over=True
        )

        requirement2 = f.ResponsibilityEducationRequirementFactory(
            responsibility=responsibility, interval_base=task_type3
        )

        requirements = self.reset.get_requirements(employee)

        self.assertIn(requirement1, requirements)
        self.assertNotIn(requirement2, requirements)

    def test_get_base_task(self):
        task_type = f.TaskTypeFactory()

        requirement = f.ResponsibilityEducationRequirementFactory(interval_base=task_type)

        employee = f.EmployeeFactory()

        f.TaskHistoryFactory(
            employee=employee,
            type=task_type,
            completion_date=datetime.datetime(2015, 5, 28, tzinfo=pytz.UTC),
        )

        history = f.TaskHistoryFactory(
            employee=employee,
            type=task_type,
            completion_date=datetime.datetime(2015, 5, 29, tzinfo=pytz.UTC),
        )

        latest = self.reset.get_base_task(employee, requirement)

        self.assertEqual(history.pk, latest.pk)

    def test_reset_employee_tasks(self):
        position = f.PositionFactory()
        responsibility = f.ResponsibilityFactory()
        position.responsibilities.add(responsibility)
        task_type1 = f.TaskTypeFactory()
        task_type1.required_for.add(responsibility)
        task_type2 = f.TaskTypeFactory()
        task_type2.required_for.add(responsibility)
        task_type2.prerequisites.add(task_type1)
        employee = f.EmployeeFactory()
        employee.positions.add(position)
        requirement = f.ResponsibilityEducationRequirementFactory(
            responsibility=responsibility, interval_base=task_type2, start_over=True
        )
        completion_date = datetime.date(2015, 2, 1)
        task2 = employee.trainings_task_set.get(type=task_type2)
        task2.complete(completion_date)
        task1 = employee.trainings_task_set.get(type=task_type1)
        task1.complete(completion_date)
        end_date = datetime.date(2015, 1, 31)
        self.reset.reset_employee_tasks(employee, requirement, end_date)
        task2 = employee.trainings_task_set.get(pk=task2.pk)
        task1 = employee.trainings_task_set.get(pk=task1.pk)
        self.assertEqual(task2.due_date, end_date)
        self.assertEqual(task1.due_date, end_date)
        prerequisites = task_type2.prerequisites.all()
        for task in employee.trainings_task_set.filter(type__in=prerequisites):
            self.assertEqual(task.due_date, end_date)


class TestEmailMonthlyReminders(object):
    def test_sends_emails(self, outbox):
        facility = f.FacilityFactory()
        f.EmployeeFactory(facility=facility, receives_emails=True)
        email_monthly_reminders()
        assert len(outbox) != 0


class TestEmailBirthdayEmailReminder(object):
    def test_sends_emails(self, outbox):
        birthday_tomorrow = (timezone.now() + relativedelta(days=1, years=-30)).date()
        facility = f.FacilityFactory()
        admin_position = f.PositionFactory(name="Administrator")

        f.EmployeeFactory(
            facility=facility,
            receives_emails=True,
            positions=[admin_position],
            email="admin@test.com",
        )
        employee = f.EmployeeFactory(
            facility=facility,
            receives_emails=True,
            date_of_birth=birthday_tomorrow,
            email="employee@test.com",
        )

        email_birthday_reminder()
        assert len(outbox) == 1
        assert outbox[0].to == ["admin@test.com"]
        assert employee.full_name in outbox[0].body


@patch("apps.sms.send_twilio_sms")
class TestSMSInPersonTrainingReminders(object):
    @pytest.fixture(autouse=True)
    def before_test(self):
        self.facility = f.FacilityFactory(is_staff_module_enabled=True, is_lms_module_enabled=True)
        self.employee = f.EmployeeFactory(facility=self.facility)

    @override_config(TRAINING_REMINDER_ACTIVE=True)
    def test_send_in_person_reminders_sms(self, send_twilio_sms):
        send_twilio_sms.return_value = 1
        now = timezone.now().replace(hour=13)
        in_two_days = now + datetime.timedelta(days=2)
        in_seven_days = now + datetime.timedelta(days=7)
        training_event = f.TrainingEventFactory(start_time=in_two_days)
        training_event.employee_tasks.set([f.TaskFactory(employee=self.employee)])
        training_event = f.TrainingEventFactory(start_time=in_seven_days)
        training_event.employee_tasks.set([f.TaskFactory(employee=self.employee)])
        with patch("django.utils.timezone.now") as mock:
            mock.return_value = now.replace(hour=13)
            reminder = SMSInPersonTrainingReminders()
            reminder.do()
        assert send_twilio_sms.call_count == 2

    @patch("django.utils.timezone.now")
    @override_config(TRAINING_REMINDER_ACTIVE=True)
    def test_send_in_4_hours_in_person_reminders_sms(self, now, send_twilio_sms):
        now.return_value = datetime.datetime(2016, 5, 24, tzinfo=pytz.UTC)
        send_twilio_sms.return_value = 1
        in_four_hours = timezone.now() + datetime.timedelta(hours=4)
        training_event = f.TrainingEventFactory(start_time=in_four_hours)
        training_event.employee_tasks.set([f.TaskFactory(employee=self.employee)])
        reminder = SMSInPersonTrainingReminders()
        reminder.do()
        assert send_twilio_sms.call_count == 1

    def test_no_send_in_person_reminders_sms(self, send_twilio_sms):
        send_twilio_sms.return_value = 1
        now = timezone.now().replace(hour=13)
        in_two_days = now + datetime.timedelta(days=3)
        in_seven_days = now + datetime.timedelta(days=8)
        training_event = f.TrainingEventFactory(start_time=in_two_days)
        training_event.employee_tasks.set([f.TaskFactory(employee=self.employee)])
        training_event = f.TrainingEventFactory(start_time=in_seven_days)
        training_event.employee_tasks.set([f.TaskFactory(employee=self.employee)])
        with patch("django.utils.timezone.now") as mock:
            mock.return_value = now.replace(hour=13)
            reminder = SMSInPersonTrainingReminders()
            reminder.do()
        assert send_twilio_sms.call_count == 0

    @patch("django.utils.timezone.now")
    def test_no_send_in_4_hours_in_person_reminders_sms(self, now, send_twilio_sms):
        now.return_value = datetime.datetime(2016, 5, 24, tzinfo=pytz.UTC)
        send_twilio_sms.return_value = 1
        in_four_hours = timezone.now() + datetime.timedelta(hours=5)
        training_event = f.TrainingEventFactory(start_time=in_four_hours)
        training_event.employee_tasks.set([f.TaskFactory(employee=self.employee)])
        reminder = SMSInPersonTrainingReminders()
        reminder.do()
        assert send_twilio_sms.call_count == 0

    @patch("django.utils.timezone.now")
    def test_no_send_if_employee_is_disabled(self, now, send_twilio_sms):
        now.return_value = datetime.datetime(2016, 5, 24, tzinfo=pytz.UTC)
        send_twilio_sms.return_value = 1
        in_four_hours = timezone.now() + datetime.timedelta(hours=4)
        training_event = f.TrainingEventFactory(start_time=in_four_hours)
        self.employee.is_active = False
        self.employee.save()
        training_event.employee_tasks.set([f.TaskFactory(employee=self.employee)])
        reminder = SMSInPersonTrainingReminders()
        reminder.do()
        assert send_twilio_sms.call_count == 0

    @patch("django.utils.timezone.now")
    def test_no_send_if_facility_staff_module_disabled(self, now, send_twilio_sms):
        now.return_value = datetime.datetime(2016, 5, 24, tzinfo=pytz.UTC)
        send_twilio_sms.return_value = 1
        in_four_hours = timezone.now() + datetime.timedelta(hours=4)
        training_event = f.TrainingEventFactory(start_time=in_four_hours)
        self.facility.is_staff_module_enabled = False
        self.facility.save()
        training_event.employee_tasks.set([f.TaskFactory(employee=self.employee)])
        reminder = SMSInPersonTrainingReminders()
        reminder.do()
        assert send_twilio_sms.call_count == 0

    @patch("django.utils.timezone.now")
    def test_no_send_if_facility_lms_module_disabled(self, now, send_twilio_sms):
        now.return_value = datetime.datetime(2016, 5, 24, tzinfo=pytz.UTC)
        send_twilio_sms.return_value = 1
        in_four_hours = timezone.now() + datetime.timedelta(hours=4)
        training_event = f.TrainingEventFactory(start_time=in_four_hours)
        self.facility.is_lms_module_enabled = False
        self.facility.save()
        training_event.employee_tasks.set([f.TaskFactory(employee=self.employee)])
        reminder = SMSInPersonTrainingReminders()
        reminder.do()
        assert send_twilio_sms.call_count == 0


@patch("apps.sms.send_twilio_sms")
class TestSMSPastDueReminders(object):
    @pytest.fixture(autouse=True)
    def before_test(self):
        self.facility = f.FacilityFactory(is_staff_module_enabled=True, is_lms_module_enabled=True)
        self.employee = f.EmployeeFactory(facility=self.facility)

    @override_config(TRAINING_REMINDER_ACTIVE=True)
    def test_send_past_due_sms(self, send_twilio_sms):
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        past_7_days = timezone.now() - datetime.timedelta(days=7)
        f.TaskFactory(due_date=tomorrow, employee=self.employee)
        f.TaskFactory(due_date=past_7_days, employee=self.employee)
        reminder = SMSPastDueReminders()
        reminder.do()
        assert send_twilio_sms.call_count == 2

    def test_no_send_past_due_sms(self, send_twilio_sms):
        today = timezone.now()
        past_8_days = timezone.now() - datetime.timedelta(days=8)
        f.TaskFactory(due_date=today, employee=self.employee)
        f.TaskFactory(due_date=past_8_days, employee=self.employee)
        reminder = SMSPastDueReminders()
        reminder.do()
        assert send_twilio_sms.call_count == 0

    def test_no_send_if_employee_is_disabled(self, send_twilio_sms):
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        past_7_days = timezone.now() - datetime.timedelta(days=7)
        f.TaskFactory(due_date=tomorrow, employee=self.employee)
        f.TaskFactory(due_date=past_7_days, employee=self.employee)
        self.employee.is_active = False
        self.employee.save()
        reminder = SMSPastDueReminders()
        reminder.do()
        assert send_twilio_sms.call_count == 0

    def test_no_send_if_facility_staff_module_disabled(self, send_twilio_sms):
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        past_7_days = timezone.now() - datetime.timedelta(days=7)
        self.facility.is_staff_module_enabled = False
        self.facility.save()
        f.TaskFactory(due_date=tomorrow, employee=self.employee)
        f.TaskFactory(due_date=past_7_days, employee=self.employee)
        reminder = SMSPastDueReminders()
        reminder.do()
        assert send_twilio_sms.call_count == 0

    def test_no_send_if_facility_lms_module_disabled(self, send_twilio_sms):
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        past_7_days = timezone.now() - datetime.timedelta(days=7)
        self.facility.is_lms_module_enabled = False
        self.facility.save()
        f.TaskFactory(due_date=tomorrow, employee=self.employee)
        f.TaskFactory(due_date=past_7_days, employee=self.employee)
        reminder = SMSPastDueReminders()
        reminder.do()
        assert send_twilio_sms.call_count == 0


@patch("apps.sms.send_twilio_sms")
class TestSMSUpcomingReminders(object):
    @pytest.fixture(autouse=True)
    def before_test(self):
        self.facility = f.FacilityFactory(is_staff_module_enabled=True, is_lms_module_enabled=True)
        self.employee = f.EmployeeFactory(facility=self.facility)

    @override_config(TRAINING_REMINDER_ACTIVE=True)
    def test_send_upcoming_reminders(self, send_twilio_sms):
        now = timezone.now()
        in_7_days = now + datetime.timedelta(days=7)
        in_14_days = now + datetime.timedelta(days=14)
        f.TaskFactory(due_date=in_7_days, employee=self.employee)
        f.TaskFactory(due_date=in_14_days, employee=self.employee)
        reminder = SMSUpcomingReminders()
        reminder.do()
        assert send_twilio_sms.call_count == 2

    def test_no_send_upcoming_reminders(self, send_twilio_sms):
        now = timezone.now()
        in_8_days = now + datetime.timedelta(days=8)
        in_15_days = now + datetime.timedelta(days=15)
        f.TaskFactory(due_date=in_8_days, employee=self.employee)
        f.TaskFactory(due_date=in_15_days, employee=self.employee)
        reminder = SMSUpcomingReminders()
        reminder.do()
        assert send_twilio_sms.call_count == 0

    def test_no_send_if_employee_is_disabled(self, send_twilio_sms):
        now = timezone.now()
        in_7_days = now + datetime.timedelta(days=7)
        in_14_days = now + datetime.timedelta(days=14)
        self.employee.is_active = False
        self.employee.save()
        f.TaskFactory(due_date=in_7_days, employee=self.employee)
        f.TaskFactory(due_date=in_14_days, employee=self.employee)
        reminder = SMSUpcomingReminders()
        reminder.do()
        assert send_twilio_sms.call_count == 0

    def test_no_send_if_facility_staff_module_disabled(self, send_twilio_sms):
        now = timezone.now()
        in_7_days = now + datetime.timedelta(days=7)
        in_14_days = now + datetime.timedelta(days=14)
        self.facility.is_staff_module_enabled = False
        self.facility.save()
        f.TaskFactory(due_date=in_7_days, employee=self.employee)
        f.TaskFactory(due_date=in_14_days, employee=self.employee)
        reminder = SMSUpcomingReminders()
        reminder.do()
        assert send_twilio_sms.call_count == 0

    def test_no_send_if_facility_lms_module_disabled(self, send_twilio_sms):
        now = timezone.now()
        in_7_days = now + datetime.timedelta(days=7)
        in_14_days = now + datetime.timedelta(days=14)
        self.facility.is_lms_module_enabled = False
        self.facility.save()
        f.TaskFactory(due_date=in_7_days, employee=self.employee)
        f.TaskFactory(due_date=in_14_days, employee=self.employee)
        reminder = SMSUpcomingReminders()
        reminder.do()
        assert send_twilio_sms.call_count == 0
