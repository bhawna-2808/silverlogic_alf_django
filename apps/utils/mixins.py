from rest_framework import serializers


class DefaultSerializer(object):
    pass


class MultiSerializerMixin(object):
    serializers = {}

    def get_serializer_class(self):
        serializer = self.serializers.get(self.request.method, None)
        if serializer is None:
            return super(MultiSerializerMixin, self).get_serializer_class()

        if serializer is DefaultSerializer:

            class _DefaultSerializer(serializers.ModelSerializer):
                class Meta:
                    model = self.model

            return _DefaultSerializer

        return serializer
