from rest_framework.routers import DefaultRouter, DynamicRoute, Route, escape_curly_brackets


class DefaultRouter(DefaultRouter):
    def _get_dynamic_route(self, route, action):
        """
        Overridden to allow use of url_name on url
        from: https://github.com/encode/django-rest-framework/blob/master/rest_framework/routers.py#L180
        """
        initkwargs = route.initkwargs.copy()
        initkwargs.update(action.kwargs)

        url_path = escape_curly_brackets(action.url_path)

        return Route(
            url=route.url.replace("{url_path}", url_path).replace("{url_name}", action.url_name),
            mapping=action.mapping,
            name=route.name.replace("{url_name}", action.url_name),
            detail=route.detail,
            initkwargs=initkwargs,
        )

    routes = [
        # List route.
        Route(
            url=r"^{prefix}{trailing_slash}$",
            mapping={"get": "list", "post": "create"},
            name="{basename}-list",
            detail=False,
            initkwargs={"suffix": "List"},
        ),
        # Dynamically generated list routes.
        # Generated using @action(detail=False) decorator
        # on methods of the viewset.
        DynamicRoute(
            url=r"^{prefix}/{url_name}{trailing_slash}$",
            name="{basename}-{url_name}",
            initkwargs={},
            detail=False,
        ),
        # Detail route.
        Route(
            url=r"^{prefix}/{lookup}{trailing_slash}$",
            mapping={
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            },
            detail=True,
            name="{basename}-detail",
            initkwargs={"suffix": "Instance"},
        ),
        # Dynamically generated detail routes.
        # Generated using @action(detail=True) decorator on methods of the viewset.
        DynamicRoute(
            url=r"^{prefix}/{lookup}/{url_name}{trailing_slash}$",
            name="{basename}-{url_name}",
            initkwargs={},
            detail=True,
        ),
    ]
