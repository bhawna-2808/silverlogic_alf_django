import logging
import re
from datetime import timedelta
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import EMPTY_VALUES
from django.utils.encoding import smart_str

from drf_extra_fields.fields import Base64FileField, Base64ImageField
from easy_thumbnails.exceptions import InvalidImageFormatError
from easy_thumbnails.files import get_thumbnailer
from img_rotate import fix_orientation
from localflavor.us.forms import USSocialSecurityNumberField as USSocialSecurityNumberFormField
from PIL import Image
from rest_framework import serializers

from apps.base.helpers import parse_string_to_timedelta, timedelta_nice_repr

logger = logging.getLogger(__name__)

phone_digits_re = re.compile(r"^(?:1-?)?(\d{3})[-\.]?(\d{3})[-\.]?(\d{4})$")


class ThumbnailImageField(Base64ImageField):
    def __init__(self, *args, **kwargs):
        self.sizes = kwargs.pop("sizes", {})
        super(ThumbnailImageField, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        data = super(ThumbnailImageField, self).to_internal_value(data)
        data = self.fix_image_orientation(data)
        return data

    def fix_image_orientation(self, data):
        image = Image.open(data)
        try:
            image = fix_orientation(image)[0]
        except ValueError:
            # image has no exif data, nothing to fix.
            data.seek(0)
            return data
        new_data = BytesIO()
        image.save(new_data, format="JPEG")
        new_data.seek(0)
        return ContentFile(new_data.read(), name=data.name)

    def to_representation(self, value):
        if not value:
            return None

        if not getattr(value, "url", None):
            # If the file has not been saved it may not have a URL.
            return None
        url = value.url
        request = self.context.get("request", None)
        if request is not None:
            url = request.build_absolute_uri(url)

        sizes = {"full_size": url}

        thumbnailer = get_thumbnailer(value)
        for name, size in list(self.sizes.items()):
            try:
                url = thumbnailer.get_thumbnail(
                    size if isinstance(size, dict) else {"size": size}
                ).url
                if request is not None:
                    url = request.build_absolute_uri(url)
                sizes[name] = url
            except InvalidImageFormatError:
                # Expected issue in local if using staging DB
                logger.exception("No image found for URL")

        return sizes


class TimedeltaField(serializers.Field):
    error_msg = 'Enter a valid time span: e.g. "3 days, 4 hours, 2 minutes"'

    def to_representation(self, time_delta):
        if isinstance(time_delta, str):
            return time_delta
        return timedelta_nice_repr(time_delta)

    def to_internal_value(self, value):
        if not value:
            return timedelta()
        try:
            return parse_string_to_timedelta(value)
        except TypeError:
            raise serializers.ValidationError(self.error_msg)


class USPhoneNumberField(serializers.CharField):
    type_name = "USPhoneNumberField"
    type_label = "phone"
    default_error_messages = {
        "invalid": "Phone numbers must be in XXX-XXX-XXXX format.",
    }

    def validate(self, value):
        # This whole thing is copy pasted from the localflavor form field so
        # that the end format could be changed to
        # (###) ###-####
        super(USPhoneNumberField, self).validate(value)
        if value in EMPTY_VALUES:
            return ""
        value = re.sub(r"(\(|\)|\s+)", "", smart_str(value))
        if not re.search(phone_digits_re, value):
            raise ValidationError(self.error_messages["invalid"])

    def to_internal_value(self, value):
        value = re.sub(r"(\(|\)|\s+)", "", smart_str(value))
        m = phone_digits_re.search(value)
        if m is None:
            return ""
        return "(%s) %s-%s" % (m.group(1), m.group(2), m.group(3))


class USSocialSecurityNumberField(serializers.CharField):
    type_name = "USSocialSecurityNumberField"
    type_label = "ssn"

    def validate(self, value):
        ssn_field = USSocialSecurityNumberFormField(required=False)
        ssn_field.clean(value)

    def to_internal_value(self, value):
        ssn_field = USSocialSecurityNumberFormField(required=False)
        return ssn_field.clean(value)


class PDFBase64File(Base64FileField):
    ALLOWED_TYPES = ["pdf"]

    def get_file_extension(self, filename, decoded_file):
        return "pdf"
