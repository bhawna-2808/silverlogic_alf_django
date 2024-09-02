import logging
from datetime import datetime

from django.conf import settings
from django.template.loader import render_to_string

from constance import config
from pytz import timezone
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from apps.base.deep_links import get_deep_link

logger = logging.getLogger(__name__)


def send_twilio_sms(phone, message):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_TOKEN)
    message = client.messages.create(body=message, from_=settings.TWILIO_PHONE, to=phone)
    return message.sid


def send_invite_sms(employee):
    try:
        deep_link = get_deep_link(employee=employee.id)
        message = render_to_string(
            "trainings/emails/invite.txt",
            {
                "full_name": employee.full_name,
                "code": employee.invite_code,
                "deep_link": deep_link,
            },
        )
        send_twilio_sms(employee.phone_number, message)
        return True
    except TwilioRestException as ex:
        logger.info("Twilio exception while sending sms: %s", ex)
        return False


def send_in_person_reminder_sms(task):
    try:
        if not config.TRAINING_REMINDER_ACTIVE:
            return False
        deep_link = get_deep_link(fallback_url=settings.BRANCHIO_FALLBACK_URL)
        employee = task.employee
        message = None
        est_time = task.scheduled_event.start_time.astimezone(timezone("US/Eastern"))
        date = est_time.strftime("%m-%d-%Y %H:%M")
        start_time = (
            datetime.strptime(date, "%m-%d-%Y %H:%M").strftime("%m-%d-%Y %I:%M %p") + " EST"
        )
        if employee.user is not None:
            message = render_to_string(
                "trainings/emails/training-event-reminder.txt",
                {
                    "first_name": employee.first_name,
                    "task_type_name": task.type.name,
                    "start_time": start_time,
                    "deep_link": deep_link,
                },
            )
        else:
            message = render_to_string(
                "trainings/emails/training-event-no-user-reminder.txt",
                {
                    "first_name": employee.first_name,
                    "task_type_name": task.type.name,
                    "start_time": start_time,
                },
            )
        send_twilio_sms(employee.phone_number, message)
        return True
    except TwilioRestException as ex:
        logger.info("Twilio exception while sending sms: %s", ex)
        return False


def send_past_due_reminder_sms(task):
    try:
        if not config.TRAINING_REMINDER_ACTIVE:
            return False
        deep_link = get_deep_link(fallback_url=settings.BRANCHIO_FALLBACK_URL)
        employee = task.employee
        message = None
        if employee.user is not None:
            message = render_to_string(
                "trainings/emails/past-due-course-reminder.txt",
                {
                    "first_name": employee.first_name,
                    "task_type_name": task.type.name,
                    "date": task.due_date,
                    "deep_link": deep_link,
                },
            )
        else:
            message = render_to_string(
                "trainings/emails/past-due-course-no-user-reminder.txt",
                {
                    "first_name": employee.first_name,
                    "task_type_name": task.type.name,
                    "date": task.due_date,
                },
            )
        send_twilio_sms(employee.phone_number, message)
        return True
    except TwilioRestException as ex:
        logger.info("Twilio exception while sending sms: %s", ex)
        return False


def send_upcoming_reminder_sms(task):
    try:
        if not config.TRAINING_REMINDER_ACTIVE:
            return False
        deep_link = get_deep_link(fallback_url=settings.BRANCHIO_FALLBACK_URL)
        employee = task.employee
        message = None
        if employee.user is not None:
            message = render_to_string(
                "trainings/emails/upcoming-course-reminder.txt",
                {
                    "first_name": employee.first_name,
                    "task_type_name": task.type.name,
                    "date": task.due_date,
                    "deep_link": deep_link,
                },
            )
        else:
            message = render_to_string(
                "trainings/emails/upcoming-course-no-user-reminder.txt",
                {
                    "first_name": employee.first_name,
                    "task_type_name": task.type.name,
                    "date": task.due_date,
                },
            )
        send_twilio_sms(employee.phone_number, message)
        return True
    except TwilioRestException as ex:
        logger.info("Twilio exception while sending sms: %s", ex)
        return False
