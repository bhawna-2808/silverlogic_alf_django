from rest_framework import mixins, viewsets

from apps.tutorials.models import TutorialVideo

from .serializers import TutorialVideoSerializer


class TutorialVideosViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = TutorialVideo.objects.all()
    serializer_class = TutorialVideoSerializer
