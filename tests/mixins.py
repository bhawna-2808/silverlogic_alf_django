import urllib.error
import urllib.parse
import urllib.request

from django.urls import reverse


class ApiMixin:
    view_name = ""
    url_kwargs = None

    def reverse(self, view_name=None, query_params=None, **kwargs):
        if self.url_kwargs is not None:
            kwargs.setdefault("kwargs", self.url_kwargs)

        if not view_name:
            view_name = self.view_name

        url = reverse(view_name, **kwargs)

        if query_params:
            for param, value in list(query_params.items()):
                if isinstance(value, list):
                    query_params[param] = ",".join(map(str, value))
            url += "?" + urllib.parse.urlencode(query_params)

        return url
