from django.utils.functional import SimpleLazyObject, cached_property


class ChildViewSetMixin(object):
    """
    Adds functionality to make a viewset a "child" of another viewset. This is useful to inherit a viewset's
    get_object functionality.
    """

    parent_viewset = None
    parent_viewset_initkwargs = {}
    parent_id_kwarg = "parent_pk"

    @cached_property
    def parent(self):
        parent = self.parent_viewset(**self.parent_viewset_initkwargs)
        parent.request = self.request
        parent.kwargs = {}
        if self.parent_id_kwarg in self.kwargs:
            parent.kwargs[parent.lookup_url_kwarg or parent.lookup_field] = self.kwargs[
                self.parent_id_kwarg
            ]

        return parent

    @cached_property
    def parent_object(self):
        """
        A cached get of the parent object. Better than calling self.parent.get_object(), as that will
        trigger a new database fetch and permission checks each time it's called.
        """
        return SimpleLazyObject(self.parent.get_object)

    def get_serializer_context(self):
        context = super(ChildViewSetMixin, self).get_serializer_context()
        context["parent_object"] = self.parent_object
        return context
