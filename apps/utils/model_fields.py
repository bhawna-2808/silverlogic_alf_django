from django.db import models


class ProperNameField(models.TextField):
    """Makes sure first letter is capital and rest are lowercase."""

    def pre_save(self, model_instance, add):
        name = super(ProperNameField, self).pre_save(model_instance, add)
        name = name[0].upper() + name[1:].lower()
        setattr(model_instance, self.attname, name)
        return name
