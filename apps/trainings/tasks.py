import datetime
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Q
from django.template.loader import render_to_string
from django.utils import timezone

import pytz
from celery import shared_task

from apps.facilities.models import FacilityUser
from apps.sms import (
    send_in_person_reminder_sms,
    send_past_due_reminder_sms,
    send_upcoming_reminder_sms,
)

from .models import (
    Employee,
    Facility,
    GlobalRequirement,
    Position,
    ResponsibilityEducationRequirement,
    Task,
    TaskHistoryStatus,
    TaskType,
    TrainingEvent,
)

logger = logging.getLogger(__name__)


def default_employee_sms_filters():
    return (
        Q(employee__is_active=True)
        & Q(employee__facility__is_staff_module_enabled=True)
        & Q(employee__facility__is_lms_module_enabled=True)
    )


class SMSInPersonTrainingReminders(object):
    def do(self):
        now = timezone.now()
        two_days = now + datetime.timedelta(days=2)
        seven_days = now + datetime.timedelta(days=7)
        four_hours = now + datetime.timedelta(hours=4)

        training_events = None
        if now.hour == 13:
            training_events = TrainingEvent.objects.filter(
                Q(
                    start_time__gte=two_days,
                    start_time__lt=two_days + datetime.timedelta(days=1),
                )
                | Q(
                    start_time__gte=seven_days,
                    start_time__lt=seven_days + datetime.timedelta(days=1),
                )
            )
        else:
            training_events = TrainingEvent.objects.filter(
                Q(
                    start_time__gte=four_hours,
                    start_time__lt=four_hours + datetime.timedelta(hours=1),
                )
            )

        if training_events:
            for training_event in training_events:
                for task in training_event.employee_tasks.filter(default_employee_sms_filters()):
                    send_in_person_reminder_sms(task)


class SMSPastDueReminders(object):
    def do(self):
        now = timezone.now()
        next_day = now + datetime.timedelta(days=1)
        current_weekday = int(now.strftime("%w")) + 1
        tasks = Task.objects.filter(default_employee_sms_filters()).filter(
            Q(due_date=next_day.date()) | Q(due_date__lt=now, due_date__week_day=current_weekday)
        )

        for task in tasks:
            send_past_due_reminder_sms(task)


class SMSUpcomingReminders(object):
    def do(self):
        now = timezone.now()
        one_week_ahead = now + datetime.timedelta(days=7)
        two_weeks_ahead = now + datetime.timedelta(days=14)
        tasks = Task.objects.filter(default_employee_sms_filters()).filter(
            Q(due_date=one_week_ahead.date()) | Q(due_date=two_weeks_ahead.date())
        )

        for task in tasks:
            send_upcoming_reminder_sms(task)


def get_emails(facility, is_admin=False, facility_user_roles=False):
    employees = Employee.objects.filter(receives_emails=True, facility=facility, is_active=True)

    if is_admin:
        employees = employees.filter(positions__name="Administrator")

    if facility_user_roles:
        employees = employees.filter(
            Q(user__facility_users__role__in=facility_user_roles)
            | Q(positions__name__in=facility_user_roles)
        ).distinct()

    employees = employees.exclude(Q(email="") | Q(email=None))
    return employees.values_list("email", flat=True)


def is_today_email_day():
    now = timezone.now()
    weekday = now.weekday()
    return weekday in (0, 2)


class EmailEmployeeEvents(object):
    def do(self):
        tomorrow_start = timezone.now().replace(hour=0, minute=0, second=0) + datetime.timedelta(
            days=1
        )
        tomorrow_end = tomorrow_start + datetime.timedelta(days=1)
        three_days_start = timezone.now().replace(hour=0, minute=0, second=0) + datetime.timedelta(
            days=3
        )
        three_days_end = three_days_start + datetime.timedelta(days=1)

        for employee in Employee.objects.filter(receives_emails=True).exclude(email=""):
            training_events_tomorrow = TrainingEvent.objects.filter(
                attendees=employee,
                start_time__gte=tomorrow_start,
                start_time__lt=tomorrow_end,
            ).order_by("start_time")
            training_events_three_days = TrainingEvent.objects.filter(
                attendees=employee,
                start_time__gte=three_days_start,
                start_time__lt=three_days_end,
            ).order_by("start_time")

            for events in [training_events_tomorrow, training_events_three_days]:
                count = events.count()
                if count:
                    context = {
                        "training_events": events,
                        "to_be": "are" if count > 1 else "is",
                        "event_word": "events" if count > 1 else "event",
                    }
                    subject = "You are enrolled for training %s" % (context["event_word"])

                    message = render_to_string(
                        "trainings/emails/scheduled_training_employees_events.txt",
                        context,
                    )

                    send_mail(
                        subject,
                        message,
                        from_email=None,
                        recipient_list=[employee.email],
                    )


class EmailScheduledTrainingsToday(object):
    def do(self):
        today_start = timezone.now().replace(hour=0, minute=0, second=0)
        tomorrow_start = today_start + datetime.timedelta(days=1)

        for facility in Facility.objects.all():
            roles = [FacilityUser.Role.account_admin, FacilityUser.Role.manager]
            admin_emails = get_emails(facility, facility_user_roles=roles)

            if admin_emails:
                training_events = TrainingEvent.objects.filter(
                    start_time__gte=today_start,
                    start_time__lt=tomorrow_start,
                    facility=facility,
                ).order_by("start_time")

                self.mail_trainings(training_events, admin_emails)

    def mail_trainings(self, training_events, admin_emails):
        count = training_events.count()
        context = {
            "training_events": training_events,
            "count": count,
            "site": settings.FRONT_URL,
        }

        if count:
            context["to_be"] = "are" if count > 1 else "is"
            context["event_word"] = "events" if count > 1 else "event"
            subject = "There %s %s training %s scheduled today" % (
                context["to_be"],
                count,
                context["event_word"],
            )
            context["subject"] = subject
            message = render_to_string(
                "trainings/emails/scheduled_training_event_today.txt", context
            )

            send_mail(subject, message, from_email=None, recipient_list=admin_emails)


class EmailOverdueTasksThisWeek(object):
    def __init__(self):
        self.now = datetime.datetime.now(pytz.timezone(settings.TIME_ZONE))

    def do(self):
        if not is_today_email_day():
            return

        for facility in Facility.objects.all():
            roles = [
                FacilityUser.Role.account_admin,
                FacilityUser.Role.manager,
                "Administrator",
                "Manager",
            ]
            admin_emails = get_emails(facility, facility_user_roles=roles)

            if admin_emails:
                expired_tasks = self.get_expired_tasks(facility)
                expiring_tasks = self.get_expiring_tasks(facility)
                status_types = []

                if expired_tasks.exists():
                    task_types_expired = TaskType.objects.prefetch_related(
                        Prefetch("task_set", queryset=expired_tasks)
                    )
                    status_types.append(("Expired", task_types_expired))

                    if expiring_tasks.exists():
                        task_types_expiring = TaskType.objects.prefetch_related(
                            Prefetch("task_set", queryset=expiring_tasks)
                        )
                        status_types.append(("Expiring", task_types_expiring))

                    if not admin_emails.filter(email__iexact=facility.contact_email).exists():
                        admin_emails = list(admin_emails)
                        admin_emails.append(facility.contact_email.lower())
                    self.mail_facility_non_compliance(status_types, admin_emails)

    def get_expired_tasks(self, facility):
        return Task.objects.select_related("employee").filter(
            due_date__lt=self.now.date(),
            employee__is_active=True,
            employee__facility=facility,
            is_optional=False,
        )

    def get_expiring_tasks(self, facility):
        return Task.objects.select_related("employee").filter(
            due_date__gte=self.now.date(),
            due_date__lte=(self.now.date() + datetime.timedelta(days=60)),
            employee__is_active=True,
            employee__facility=facility,
            is_optional=False,
        )

    def mail_facility_non_compliance(self, status_types, admin_emails):
        subject = "Compliance Issues"
        message = render_to_string(
            "trainings/emails/facility_non_compliant.txt",
            {"status_types": status_types, "site": settings.FRONT_URL},
        )

        send_mail(subject, message, from_email=None, recipient_list=admin_emails)


class EmailFacilityCompliant(object):
    def __init__(self):
        self.now = timezone.localtime(timezone.now())

    def do(self):
        if not is_today_email_day():
            return

        for facility in Facility.objects.all():
            admin_emails = get_emails(facility)
            overdue_tasks_exist = self.overdue_tasks_exist(facility)

            if admin_emails and not overdue_tasks_exist:
                now_date = self.now.date()
                ninety_days = now_date + datetime.timedelta(days=90)
                ninety_day_tasks = Task.objects.select_related("employee").filter(
                    due_date__gte=now_date,
                    due_date__lt=ninety_days,
                    employee__is_active=True,
                    employee__facility=facility,
                    is_optional=False,
                )
                task_types = TaskType.objects.prefetch_related(
                    Prefetch("task_set", queryset=ninety_day_tasks)
                )
                self.mail_facility_compliance(task_types, admin_emails)

    def mail_facility_compliance(self, task_types, admin_emails):
        subject = "Your facility is compliant"
        message = render_to_string(
            "trainings/emails/facility_compliant.txt",
            {"task_types": task_types, "site": settings.FRONT_URL},
        )

        send_mail(subject, message, from_email=None, recipient_list=admin_emails)

    def overdue_tasks_exist(self, facility):
        return (
            Task.objects.select_related("employee")
            .filter(
                due_date__lt=self.now.date(),
                employee__is_active=True,
                employee__facility=facility,
                is_optional=False,
            )
            .exists()
        )


class EmailCompletedTrainingsReminderToday(object):
    def do(self):
        today_start = timezone.now().replace(hour=0, minute=0, second=0)
        yesterday_start = today_start - datetime.timedelta(days=1)

        for facility in Facility.objects.all():
            roles = [FacilityUser.Role.account_admin, FacilityUser.Role.manager]
            admin_emails = get_emails(facility, facility_user_roles=roles)

            if admin_emails:
                training_events = TrainingEvent.objects.filter(
                    end_time__gte=yesterday_start,
                    end_time__lt=today_start,
                    facility=facility,
                ).select_related("training_for", "facility")

                self.mail_trainings(training_events, admin_emails)

    def mail_trainings(self, training_events, admin_emails):
        for training_event in training_events:
            subject = "Mark Who Completed %s: Event" % training_event.training_for.name
            context = {"training_event": training_event, "site": settings.FRONT_URL}
            message = render_to_string(
                "trainings/emails/completed_trainings_reminder_today.txt", context
            )

            send_mail(subject, message, from_email=None, recipient_list=admin_emails)


class ResetPrerequisiteTasks(object):
    """
        Resets the due dates of interval bases and their prerequisites if the
    employee failed to meet the education requirements
    """

    def __init__(self):
        self.now_date = timezone.localtime(timezone.now()).date()

    def do(self):
        """
        Executes the cron job
        """
        for facility in Facility.objects.all():
            employees = facility.employee_set.all()
            for employee in employees:
                requirements = self.get_requirements(employee)
                for requirement in requirements:
                    base_task = self.get_base_task(employee, requirement)
                    if base_task:
                        end_date = base_task.completion_date + requirement.timeperiod
                        satisfied = self.has_satisfied_requirement(
                            employee, requirement, base_task.completion_date, end_date
                        )
                        if (self.now_date > end_date) and not satisfied:
                            self.reset_employee_tasks(employee, requirement, end_date)

    def get_requirements(self, employee):
        """
            Returns the employee's requirements with interval bases that start
        over
        """
        responsibilities = employee.other_responsibilities.all()

        return ResponsibilityEducationRequirement.objects.filter(start_over=True).filter(
            responsibility__in=responsibilities
        )

    def get_base_task(self, employee, requirement):
        """
            Returns the `TaskHistory` entry for the last interval base
        completion
        """
        return (
            employee.trainings_taskhistory_set.filter(status=TaskHistoryStatus.completed)
            .filter(type_id=requirement.interval_base.id)
            .last()
        )

    def has_satisfied_requirement(self, employee, requirement, start_date, end_date):
        """
            Returns True if the employee has satisfied the required hours for
        the requirement within the timespan specified.
        """
        task_history = (
            employee.trainings_taskhistory_set.filter(status=TaskHistoryStatus.completed)
            .filter(completion_date__gte=start_date)
            .filter(completion_date__lt=end_date)
        )
        accumulated_hours = 0
        for task in task_history:
            for credit in task.type.education_credits.filter(type=requirement.type):
                accumulated_hours += task.credit_hours

        return accumulated_hours == requirement.hours

    def reset_employee_tasks(self, employee, requirement, end_date):
        """
        Resets the due date of the interval base task and its prerequisites
        """
        base_task = employee.trainings_task_set.filter(type=requirement.interval_base).first()
        if base_task:
            self.recurse_reset(base_task, end_date)

    def recurse_reset(self, task, end_date, task_id_set=set()):
        """
            Recursively resets a task and its prerequisites. Does not process
        previously processed tasks to avoid recursion error in case there are
        circular prerequisites.
        """
        if task.id not in task_id_set:
            task_id_set.add(task.id)
            if task.due_date > end_date:
                task.due_date = end_date
                task.save()
            prerequisites = task.type.prerequisites.values_list("pk", flat=True)
            tasks = Task.objects.filter(type_id__in=prerequisites)
            for task in tasks:
                self.recurse_reset(task, end_date)


@shared_task
def email_employee_events():
    EmailEmployeeEvents().do()


@shared_task
def email_scheduled_trainings_today():
    EmailScheduledTrainingsToday().do()


@shared_task
def email_overdue_tasks_this_week():
    EmailOverdueTasksThisWeek().do()


@shared_task
def email_facility_compliant():
    EmailFacilityCompliant().do()


@shared_task
def email_completed_trainings_reminder_today():
    EmailCompletedTrainingsReminderToday().do()


@shared_task
def reset_prerequisite_tasks():
    ResetPrerequisiteTasks().do()


@shared_task
def sms_in_person_training_reminders():
    SMSInPersonTrainingReminders().do()


@shared_task
def sms_past_due_reminders():
    SMSPastDueReminders().do()


@shared_task
def sms_upcoming_reminders():
    SMSUpcomingReminders().do()


@shared_task
def email_monthly_reminders():
    for facility in Facility.objects.all():
        admin_emails = get_emails(facility)
        subject = render_to_string("trainings/emails/monthly-reminder-subject.txt").strip()
        message = render_to_string("trainings/emails/monthly-reminder-body.txt")
        send_mail(subject, message, from_email=None, recipient_list=admin_emails)


@shared_task
def email_birthday_reminder():
    tomorrow = (timezone.now() + datetime.timedelta(days=1)).date()
    for employee in Employee.objects.filter(
        is_active=True,
        date_of_birth__month=tomorrow.month,
        date_of_birth__day=tomorrow.day,
    ):
        admin_emails = get_emails(employee.facility, is_admin=True)
        admin_emails = admin_emails.exclude(email=employee.email)

        subject = render_to_string("trainings/emails/birthday-reminder-subject.txt").strip()
        message = render_to_string(
            "trainings/emails/birthday-reminder-body.txt",
            {
                "full_name": employee.full_name,
            },
        )
        send_mail(subject, message, from_email=None, recipient_list=admin_emails)


@shared_task
def reapply_employee_positions(employee_id=None):
    if employee_id:
        queryset = Employee.objects.filter(pk=employee_id)
    else:
        queryset = Employee.objects.all()
    for employee in queryset:
        with transaction.atomic():
            positions = [p for p in employee.positions.all()]
            employee.positions.set([])
            employee.positions.set(positions)


@shared_task
def reapply_position(position_id):
    position = Position.objects.get(pk=position_id)
    for employee in Employee.objects.filter(positions=position):
        employee.positions.remove(position)
        employee.positions.add(position)


@shared_task
def reapply_employee_responsibilities(employee_id=None):
    if employee_id:
        queryset = Employee.objects.filter(pk=employee_id)
    else:
        queryset = Employee.objects.all()
    for employee in queryset:
        with transaction.atomic():
            responsibilities = [r for r in employee.other_responsibilities.all()]
            employee.other_responsibilities.set([])
            employee.other_responsibilities.set(responsibilities)


@shared_task
def apply_global_requirement(global_requirement_id):
    global_requirement = GlobalRequirement.objects.filter(pk=global_requirement_id).first()
    for employee in Employee.objects.all():
        task_type = global_requirement.task_type
        if task_type.check_capacity(employee):
            with transaction.atomic():
                task, _ = Task.objects.get_or_create(
                    employee=employee, type=global_requirement.task_type
                )
                task.recompute_due_date()


@shared_task
def apply_type_responsibility(pk_set, task_type_id):
    task_type = TaskType.objects.get(id=task_type_id)
    # Affected positions.
    positions = Position.objects.filter(responsibilities__id__in=pk_set).distinct()

    employees = Employee.objects.filter(
        Q(other_responsibilities__id__in=pk_set) | Q(positions__in=positions)
    ).distinct()

    for employee in employees:
        with transaction.atomic():
            task, _ = Task.objects.get_or_create(employee=employee, type=task_type)
            task.recompute_due_date()


@shared_task
def deactivate_employees_after_termination_date():
    employees_to_deactivate = Employee.objects.filter(
        is_active=True, deactivation_date__lte=timezone.now(), is_reactivated=False
    )
    if employees_to_deactivate.exists():
        employees_to_deactivate.update(is_active=False)


@shared_task
def regenerate_task_certificates(facility_pk):
    from ..api.trainings.views import generate_course_certificate

    obj = Facility.objects.filter(pk=facility_pk).first()
    if obj:
        for employee in obj.employee_set.all():
            completed_courses = employee.courses.filter(completed_date__isnull=False)
            [
                *map(
                    lambda x: x.certificate.delete(),
                    employee.trainings_taskhistory_set.filter(certificate__isnull=False),
                )
            ]
            for ec in completed_courses:
                try:
                    course = ec.course
                    task = course.task_type.task_set.filter(employee=employee).first()
                    th = employee.trainings_taskhistory_set.filter(type=task.type).first()
                    generate_course_certificate(employee, obj, th, ec)
                except (AttributeError, IntegrityError) as e:
                    logger.error(
                        f"Error when regenerating certificate for {employee} for course {ec}: {e}"
                    )
