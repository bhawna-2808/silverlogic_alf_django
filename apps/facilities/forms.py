from django.forms import ModelChoiceField, ModelForm

from ..trainings.models import Facility
from .models import FacilityUser


class FacilityUserForm(ModelForm):
    facility = ModelChoiceField(queryset=Facility.objects.order_by("name"))

    class Meta:
        model = FacilityUser
        fields = "__all__"
