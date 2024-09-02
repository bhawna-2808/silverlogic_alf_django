from django import forms

from apps.trainings.models import Trainer


class TrainerForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = (
            "first_name",
            "last_name",
            "signature",
            "contact_info",
            "endorsements",
        )

    def clean(self):
        errors = {}

        contact_info = self.cleaned_data.get("contact_info")
        endorsements = self.cleaned_data.get("endorsements")

        if len(contact_info.splitlines()) > 5:
            errors["contact_info"] = "Contact info should have 5 lines or less"

        if len(endorsements.splitlines()) > 12:
            errors["endorsements"] = "Endorsements info should have 12 lines or less"

        if errors:
            raise forms.ValidationError(errors)
