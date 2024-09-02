from apps.facilities.models import FacilityUser


class BaseNotManager:
    def has_object_permission(self, request, view, obj):
        return True


class NotManagerOrCanAccessResidents(BaseNotManager):
    def has_permission(self, request, view):
        facility_user = request.user.facility_users

        if facility_user.role != FacilityUser.Role.manager:
            return True

        return facility_user.can_see_residents


class NotManagerOrCanAccessStaff(BaseNotManager):
    def has_permission(self, request, view):
        facility_user = request.user.facility_users

        if facility_user.role != FacilityUser.Role.manager:
            return True

        return facility_user.can_see_staff
