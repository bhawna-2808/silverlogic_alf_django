from apps.facilities.models import FacilityUser
from apps.facilities.tokens import UserInviteTokenGenerator

from ..permissions import IsRole


class IsAccountAdminOrManagerOrHasRetrieveToken(
    IsRole(FacilityUser.Role.account_admin, FacilityUser.Role.manager)
):
    def has_permission(self, request, view):
        if not request.user.is_authenticated and getattr(view, "action", "") == "retrieve":
            return True
        return super(IsAccountAdminOrManagerOrHasRetrieveToken, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated and getattr(view, "action", "") == "retrieve":
            token = request.query_params.get("token", "")
            return UserInviteTokenGenerator().check_token(invite=obj, token=token)
        return super(IsAccountAdminOrManagerOrHasRetrieveToken, self).has_object_permission(
            request, view, obj
        )
