import warnings

from rest_framework import status
from rest_framework.response import Response


class DestroyModelMixin:
    """Destroy mixin that returns empty object as response.

    iOS requires that every response contains a JSON serializable
    object because of the framework they use.

    """

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({}, status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()


class DynamicFieldsMixin(object):
    """
    A serializer mixin that takes an additional `fields` argument that controls
    which fields should be displayed.
    """

    @property
    def fields(self):
        """
        Filters the fields according to the `fields` query parameter.
        A blank `fields` parameter (?fields) will remove all fields. Not
        passing `fields` will pass all fields individual fields are comma
        separated (?fields=id,name,url,email).
        """
        fields = super(DynamicFieldsMixin, self).fields

        if not hasattr(self, "_context"):
            # We are being called before a request cycle
            return fields

        # Only filter if this is the root serializer, or if the parent is the
        # root serializer with many=True
        is_root = self.root == self
        parent_is_list_root = self.parent == self.root and getattr(self.parent, "many", False)
        if not (is_root or parent_is_list_root):
            return fields

        try:
            request = self.context["request"]
        except KeyError:
            warnings.warn("Context does not have access to request")
            return fields

        # NOTE: drf test framework builds a request object where the query
        # parameters are found under the GET attribute.
        params = getattr(request, "query_params", getattr(request, "GET", None))
        if params is None:
            warnings.warn("Request object does not contain query paramters")

        try:
            filter_fields = params.get("fields", None).split(",")
        except AttributeError:
            filter_fields = None

        # Drop any fields that are not specified in the `fields` argument.
        existing = set(fields.keys())
        if filter_fields is None:
            # no fields param given, don't filter.
            allowed = existing
        else:
            allowed = set([_f for _f in filter_fields if _f])

        for field in existing:

            if field not in allowed:
                fields.pop(field, None)

        return fields
