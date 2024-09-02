import os
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

import phonenumbers


class CaseInsensitiveTextField(models.TextField):
    description = _("Case insensitive text")

    def db_type(self, connection):
        return "citext"


class CaseInsensitiveEmailField(CaseInsensitiveTextField, models.EmailField):
    description = _("Case insensitive email address")


def validate_us_phone_number(value):
    parsed = phonenumbers.parse(value, "US")
    if not phonenumbers.is_valid_number(parsed):
        raise ValidationError("Number is not a valid US number!")
    return True


class UsPhoneNumberField(models.CharField):
    def __init__(self, max_length=50, *args, **kwargs):
        validators = [validate_us_phone_number]
        # When loading migrations the validate_us_phone_number will be passed to this init
        if "validators" in kwargs and validate_us_phone_number not in kwargs["validators"]:
            validators = [*kwargs["validators"], *validators]
            del kwargs["validators"]
        elif "validators" in kwargs:
            validators = kwargs["validators"]
            del kwargs["validators"]
        return super().__init__(*args, validators=validators, max_length=max_length, **kwargs)

    def get_db_prep_save(self, value, connection, prepared=False):
        if not bool(value):
            return ""
        return phonenumbers.format_number(
            phonenumbers.parse(value, "US"), phonenumbers.PhoneNumberFormat.NATIONAL
        )


@deconstructible
class random_name_in(object):
    def __init__(self, dir):
        self.dir = dir

    def __call__(self, instance, filename):
        ext = filename.split(".")[-1]
        filename = "{}.{}".format(uuid.uuid4(), ext)
        return os.path.join(self.dir, filename)


class PdfParameters(models.Model):
    """
    Used for store parameters from a post request before a get request
    that actually generates the pdf
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parameters = models.TextField()  # will be a json dump of the post data
