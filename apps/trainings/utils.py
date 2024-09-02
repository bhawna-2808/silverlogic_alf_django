import os

from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string

from .tasks import get_emails


def send_custom_task_type_mail(custom_task_type, admin_url):
    subject = "New custom task type request"
    to_email = settings.CUSTOM_TASK_TYPE_ADMIN_EMAIL
    context = {"name": custom_task_type.name, "admin_url": admin_url}
    message = render_to_string("trainings/emails/custom_task_type_request.txt", context)

    send_mail(subject, message, from_email=None, recipient_list=[to_email])


def send_certificate_to_admins(employee, task_name, facility, pages):
    admin_emails = get_emails(facility, is_admin=True)
    context = {"employee_name": employee.full_name, "training_name": task_name}
    subject = render_to_string("trainings/emails/completed-training-subject.txt", context).strip()
    message = render_to_string("trainings/emails/completed-training-body.txt", context)
    email = EmailMultiAlternatives(subject, message, from_email=None, to=admin_emails)
    for page in pages:
        attach_pdf_to_email(email, page)
    email.send()


def attach_pdf_to_email(email, page):
    # Dear future developer: if you look at this and think wait this is useless, you are RIGHT
    # but damn tests fail on server if i don't override somehow the path see
    # test_complete_course_create_taskhistory_and_certificate
    storage = DefaultStorage()
    with storage.open(page.page.name) as page_file:
        email.attach(os.path.basename(page_file.name), page_file.read())
