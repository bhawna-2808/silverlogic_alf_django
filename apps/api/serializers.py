from django.db import models
from django.db.models import DurationField as ModelTimedeltaField

from rest_framework.serializers import ModelSerializer as OrigModelSerializer

from .fields import ThumbnailImageField, TimedeltaField


class ModelSerializer(OrigModelSerializer):
    def build_url_field(self, field_name, model_class):
        """
        Create a field representing the object's own URL.
        """
        field_class = self.serializer_url_field
        field_kwargs = {
            "view_name": "{model_name}s-detail".format(
                model_name=model_class._meta.object_name.lower()
            )
        }
        return field_class, field_kwargs


ModelSerializer.serializer_field_mapping[models.ImageField] = ThumbnailImageField
ModelSerializer.serializer_field_mapping[ModelTimedeltaField] = TimedeltaField


class AutoFacilityMixin(object):
    def create(self, validated_data):
        validated_data["facility"] = self.context["request"].facility
        return super(AutoFacilityMixin, self).create(validated_data)
