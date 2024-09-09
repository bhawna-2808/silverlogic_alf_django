from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.contrib.auth.models import Group
from django.urls import re_path
from actstream.models import Action, Follow
from apps.activities.admin import DashboardAdmin
from apps.activities.models import Activity

admin.autodiscover()

# Unregister models only if they are registered
if Group in admin.site._registry:
    admin.site.unregister(Group)

if Action in admin.site._registry:
    admin.site.unregister(Action)

if Follow in admin.site._registry:
    admin.site.unregister(Follow)

urlpatterns = [
    re_path(
        r"^admin/dashboard",
        DashboardAdmin(Activity, admin.site).changelist_view,
        name="dashboard",
    ),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^api/", include("apps.api.urls")),
    # Stripe
    re_path(r"^stripe/", include("djstripeevents.urls")),
    re_path(r"^backend/", include("backend_admin.urls")),
]

if settings.DEBUG:
    from urllib.parse import urlparse
    from django.conf.urls.static import static

    media_url = urlparse(settings.MEDIA_URL)
    static_url = urlparse(settings.STATIC_URL)
    urlpatterns += static(media_url.path, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(static_url.path, document_root=settings.STATIC_ROOT)
