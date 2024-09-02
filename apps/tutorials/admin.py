from django.contrib import admin

from embed_video.admin import AdminVideoMixin
from ordered_model.admin import OrderedModelAdmin

from .models import TutorialVideo


class TutorialVideoAdmin(AdminVideoMixin, OrderedModelAdmin):
    list_display = ("title", "url", "move_up_down_links")


admin.site.register(TutorialVideo, TutorialVideoAdmin)
