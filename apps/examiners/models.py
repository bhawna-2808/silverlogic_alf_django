from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string

from django_fsm import FSMField
from model_utils import Choices
from model_utils.models import TimeStampedModel


class Examiner(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name="examiner", on_delete=models.CASCADE
    )
    medical_license_number = models.CharField(max_length=25, blank=True)

    def __repr__(self):
        return "<Examiner pk={}>".format(self.pk)

    def __str__(self):
        return str(self.user)


class ResidentAccess(TimeStampedModel):
    examiner = models.ForeignKey("Examiner", related_name="residents", on_delete=models.CASCADE)
    resident = models.ForeignKey(
        "residents.Resident", related_name="examiners", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name_plural = "resident accesses"

    def __repr__(self):
        return "<ResidentAccess pk={}>".format(self.pk)

    def __str__(self):
        return "{} has access to {}".format(self.examiner, self.resident)


class ExaminationRequest(TimeStampedModel):
    Status = Choices("sent", "examined")

    examiner = models.ForeignKey(
        "Examiner", related_name="examination_requests", on_delete=models.CASCADE
    )
    resident = models.ForeignKey(
        "residents.Resident",
        related_name="examination_requests",
        on_delete=models.CASCADE,
    )
    status = FSMField(choices=Status, default=Status.sent)

    class Meta:
        verbose_name_plural = "examination requests"

    def __repr__(self):
        return "<ExaminationRequest pk={}>".format(self.pk)

    def __str__(self):
        return "{} has been requested to examine {}".format(self.examiner, self.resident)

    def save(self, *args, **kwargs):
        is_create = False
        if not self.pk:
            is_create = True
        super(ExaminationRequest, self).save(*args, **kwargs)
        if is_create:
            self.send()

    def send(self):
        context = {
            "facility": self.resident.facility,
            "url": settings.FRONT_USER_RESIDENT_1823_URL.format(id=self.resident.pk),
        }
        subject = render_to_string(
            "examiners/emails/request-examination-subject.txt", context
        ).strip()
        message = render_to_string("examiners/emails/request-examination-body.txt", context)
        html_message = render_to_string("examiners/emails/request-examination-body.html", context)
        send_mail(
            subject,
            message,
            from_email=None,
            recipient_list=[self.examiner.user.email],
            html_message=html_message,
        )
