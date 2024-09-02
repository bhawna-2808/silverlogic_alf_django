from django.db import models

from embed_video.fields import EmbedVideoField
from ordered_model.models import OrderedModel


class TutorialVideo(OrderedModel):
    title = models.CharField(max_length=100)
    url = EmbedVideoField()
    description = models.TextField()

    def __str__(self):
        return 'Tutorial Video "{}"'.format(self.title)

    def __repr__(self):
        return "<TutorialVideo: {}>".format(self.pk)
