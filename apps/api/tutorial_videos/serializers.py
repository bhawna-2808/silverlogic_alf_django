from embed_video.backends import detect_backend
from rest_framework import serializers

from apps.tutorials.models import TutorialVideo


class TutorialVideoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = TutorialVideo
        fields = (
            "title",
            "description",
            "url",
        )

    def get_url(self, obj):
        return detect_backend(obj.url).get_url()
