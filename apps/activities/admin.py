from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse


class ContentTypeFilter(admin.SimpleListFilter):
    def __init__(self, request, params, model, model_admin):
        self.separator = "-"
        self.title = "Action Type"
        self.parameter_name = "action_type"
        self.content_type_id_field = "action_object_content_type_id"
        super(ContentTypeFilter, self).__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):
        qs = (
            model_admin.model.objects.all()
            .order_by(self.content_type_id_field)
            .distinct(self.content_type_id_field)
            .values_list(self.content_type_id_field, flat=True)
        )
        return [
            (
                content_type_id,
                ContentType.objects.get(id=content_type_id).model_class().__name__,
            )
            for content_type_id in qs
        ]

    def queryset(self, request, queryset):
        content_type_id = self.value()
        if content_type_id:
            return queryset.filter(**{self.content_type_id_field: content_type_id})
        else:
            return queryset


class DashboardAdmin(admin.ModelAdmin):
    change_list_template = "admin/dashboard/dashboard.html"
    list_filter = [ContentTypeFilter]
    list_display = (
        "timestamp",
        "get_description",
    )
    list_display_links = None
    actions = None

    def has_add_permission(self, request):
        return False

    def get_description(self, obj):
        description = "{actor} {verb}".format(
            actor=self.get_admin_link_for_generic_foreign_key(
                obj, "actor_content_type_id", "actor_object_id"
            ),
            verb=obj.verb,
        )
        action_object = self.get_admin_link_for_generic_foreign_key(
            obj, "action_object_content_type_id", "action_object_object_id"
        )
        if obj.actor_content_type_id != obj.action_object_content_type_id and action_object:
            description += " {}".format(action_object)

        target = self.get_admin_link_for_generic_foreign_key(
            obj, "target_content_type_id", "target_object_id"
        )
        if target:
            description += " ({})".format(target)

        return description

    get_description.allow_tags = True
    get_description.short_description = "Description"

    def get_admin_link_for_generic_foreign_key(self, obj, content_type_id_field, object_id_field):
        content_type_id = getattr(obj, content_type_id_field)
        object_id = getattr(obj, object_id_field)
        if content_type_id and object_id:
            model_class = ContentType.objects.get(id=content_type_id).model_class()
            model = model_class.objects.get(id=object_id)
            link = reverse(
                "admin:%s_%s_change" % (model._meta.app_label, model._meta.model_name),
                args=(model.id,),
            )
            try:
                return '<a href="%s">%s</a>' % (
                    link,
                    model.get_full_name() or model.email if isinstance(model, User) else str(model),
                )
            except UnicodeDecodeError:
                return str(str(model).decode("unicode-escape"))
        return ""
