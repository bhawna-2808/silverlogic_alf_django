from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from django_fsm import FSMField, transition
from model_utils import Choices
from model_utils.models import TimeStampedModel
from timed_auth_token.models import TimedAuthToken

from apps.base.models import CaseInsensitiveEmailField, UsPhoneNumberField, random_name_in
from apps.examiners.models import Examiner, ResidentAccess

from .tokens import UserInviteTokenGenerator


class FacilityUser(models.Model):
    Role = Choices(
        # Can do everything.
        ("account_admin", _("Account Administrator")),
        # Can do everything except manage users.
        ("manager", _("Manager")),
        # A medical examiner.  Deals only with residents.
        ("examiner", _("Medical Examiner")),
        # An Employee with trainings access. (Trainings webapp / Mobile apps)
        ("trainings_user", _("Trainings User")),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="facility_users",
        on_delete=models.CASCADE,
    )
    facility = models.ForeignKey(
        "trainings.Facility", related_name="facility_users", on_delete=models.CASCADE
    )
    role = models.CharField(max_length=255, choices=Role)
    can_see_residents = models.BooleanField(default=True)
    can_see_staff = models.BooleanField(default=True)

    def __str__(self):
        return "{} - {}".format(self.facility, self.user)

    def __repr__(self):
        return "<FacilityUser {}>".format(self.pk)


class UserInvite(TimeStampedModel):
    Role = Choices(
        ("manager", _("Manager")),
        ("examiner", _("Medical Examiner")),
        ("trainings_user", _("Trainings User")),
    )
    Status = Choices("sent", "accepted")

    facility = models.ForeignKey(
        "trainings.Facility", related_name="invites", on_delete=models.CASCADE
    )
    employee = models.ForeignKey(
        "trainings.Employee",
        related_name="invites",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    email = CaseInsensitiveEmailField()
    phone_number = UsPhoneNumberField(blank=True, max_length=50)
    role = models.CharField(max_length=255, choices=Role)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="invites", on_delete=models.CASCADE
    )
    status = FSMField(choices=Status, default=Status.sent)
    can_see_residents = models.BooleanField(default=True)
    can_see_staff = models.BooleanField(default=True)

    class Meta:
        unique_together = ["facility", "email"]

    def __str__(self):
        return "Invite for {} to {} by {} to become a {}".format(
            self.facility, self.email, self.invited_by, self.Role[self.role]
        )

    def __repr__(self):
        return "<UserInvite {}>".format(self.pk)

    def save(self, *args, **kwargs):
        is_create = False
        if not self.pk:
            is_create = True
        super(UserInvite, self).save(*args, **kwargs)
        if is_create:
            self.send()

    def send(self):
        email = getattr(self.employee, "email", self.email)
        if email == "":
            email = self.email

        # send email invite
        context = {
            "facility": self.facility,
            "invited_by": self.invited_by,
            "role": self.Role[self.role],
            "url": settings.FRONT_USER_INVITE_ACCEPT_URL.format(
                id=self.id, token=UserInviteTokenGenerator().make_token(self)
            ),
        }
        subject = render_to_string(
            "facilities/emails/user-invite-send-subject.txt", context
        ).strip()
        message = render_to_string("facilities/emails/user-invite-send-body.txt", context)
        html_message = render_to_string("facilities/emails/user-invite-send-body.html", context)
        send_mail(
            subject,
            message,
            from_email=None,
            recipient_list=[email],
            html_message=html_message,
        )

    @transition(field=status, source=Status.sent, target=Status.accepted)
    def accept(self, username, password, first_name, last_name, medical_license_number=None):
        User = get_user_model()
        user = User.objects.create_user(
            username=username,
            password=password,
            email=self.email,
            first_name=first_name,
            last_name=last_name,
        )
        FacilityUser.objects.create(
            user=user,
            facility=self.facility,
            role=self.role,
            can_see_residents=self.can_see_residents,
            can_see_staff=self.can_see_staff,
        )
        if self.employee:
            self.employee.user = user
            self.employee.code_verified = True
            self.employee.save()

        if self.role == self.Role.examiner:
            examiner = Examiner.objects.create(
                user=user, medical_license_number=medical_license_number
            )
            ResidentAccess.objects.bulk_create(
                [
                    ResidentAccess(examiner=examiner, resident=invite_access.resident)
                    for invite_access in self.resident_accesses.all()
                ]
            )

        return user


class UserInviteResidentAccess(models.Model):
    invite = models.ForeignKey(
        "UserInvite", related_name="resident_accesses", on_delete=models.CASCADE
    )
    resident = models.ForeignKey(
        "residents.Resident", related_name="user_invites", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ["invite", "resident"]
        verbose_name_plural = "invite resident accesses"

    def __repr__(self):
        return "<UserInviteResidentAccess pk={}>".format(self.pk)


class UserResidentAccess(TimeStampedModel):
    user = models.ForeignKey(
        FacilityUser, related_name="user_resident_access", on_delete=models.CASCADE
    )
    resident = models.ForeignKey(
        "residents.Resident",
        related_name="user_resident_access",
        on_delete=models.CASCADE,
    )

    # If UserResidentAccess does not exist, access is allowed
    is_allowed = models.BooleanField(default=True)

    class Meta:
        unique_together = ["user", "resident"]
        verbose_name_plural = "user resident accesses"

    def __repr__(self):
        return "<UserResidentAccess pk={}>".format(self.pk)


class BusinessAgreement(models.Model):
    facility = models.OneToOneField("trainings.Facility", on_delete=models.CASCADE)
    signed_on = models.DateTimeField(auto_now=True)
    signed_by = models.ForeignKey("FacilityUser", on_delete=models.CASCADE)
    pdf = models.FileField(upload_to=random_name_in("facilities/business-agreements"))

    def __str__(self):
        return "{}'s Business Agreement, signed by {} {}".format(
            self.facility, self.signed_by.user.first_name, self.signed_by.user.last_name
        )

    def __repr__(self):
        return "<BusinessAgreement {}>".format(self.pk)


class TrainingsTimedAuthToken(TimedAuthToken):
    """
    Trainings TimedAuthToken should never expire regardless of user role
    """

    class Meta:
        proxy = True

    allowed_roles = [
        FacilityUser.Role.trainings_user,
        FacilityUser.Role.account_admin,
        FacilityUser.Role.manager,
    ]

    @property
    def is_expired(self):
        if hasattr(self.user, "facility_users"):
            if self.user.facility_users.role in self.allowed_roles:
                return False  # Never expire tokens any ALF user in trainings
        return super().is_expired
