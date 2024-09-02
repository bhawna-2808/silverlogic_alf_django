from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.facilities.models import FacilityUser
from apps.subscriptions.models import Plan, Subscription


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request, "facility", None)


def IsRole(*roles):
    class IsRole(IsAuthenticated):
        def has_permission(self, request, view):
            if not super(IsRole, self).has_permission(request, view):
                return False
            return request.role in roles

    return IsRole


def IsRoleOrReadOnly(*roles):
    class IsRoleOrReadOnly(BasePermission):
        def has_permission(self, request, view):
            if request.method in SAFE_METHODS:
                return True
            return request.user and request.user.is_authenticated and request.role in roles

    return IsRoleOrReadOnly


def IsRoleFor(*roles, **kwargs):
    methods = kwargs.get("methods")
    assert methods

    class IsRoleFor(BasePermission):
        def has_permission(self, request, view):
            if request.method in methods:
                return request.user and request.user.is_authenticated and request.role in roles
            return True

    return IsRoleFor


def IsRoleForUpdate(*roles):
    class IsRoleForUpdate(BasePermission):
        def has_permission(self, request, view):
            if request.method in ("PUT", "PATCH"):
                return request.user and request.user.is_authenticated and request.role in roles
            return True

    return IsRoleForUpdate


class IsSameFacility(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.facility == request.facility


class IsSameFacilityForEditing(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            if not request.user.is_superuser:
                return obj.facility == request.facility

        return True


class NonEmployeeUserEditing(BasePermission):
    def has_permission(self, request, view):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            if request.user.facility_users.role == FacilityUser.Role.trainings_user:
                return False
            try:
                if request.user.employee:
                    return False
            except Exception:
                return True

        return True


class IsExternalClient(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated


class FacilityHasResidentSubscription(BasePermission):
    message = "no_resident_subscription"

    def has_permission(self, request, view):
        facility = request.facility
        subscription = Subscription.objects.current().filter(
            facility=facility, billing_interval__plan__module=Plan.Module.resident
        )
        if (subscription.exists() or facility.fcc_signup) and not hasattr(
            facility, "businessagreement"
        ):
            self.message = "business_agreement_not_signed"

        return (
            facility.fcc_signup and hasattr(facility, "businessagreement")
        ) or subscription.is_active().exists()

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class FacilityHasStaffSubscriptionIfRequired(BasePermission):
    message = "staff_subscription_required"
    max_free_employee_count = 15

    def has_permission(self, request, view):
        facility = request.facility
        has_any_subscription = Subscription.objects.filter(
            facility=facility, billing_interval__plan__module=Plan.Module.staff
        ).exists()
        if not has_any_subscription and not getattr(facility, "fcc_signup", False):
            self.message = "trial_staff_subscription_required"
            return False

        if facility.employee_set.filter(is_active=True).count() > self.max_free_employee_count:
            has_subscription = (
                Subscription.objects.current()
                .filter(facility=facility, billing_interval__plan__module=Plan.Module.staff)
                .is_active()
                .exists()
            )
            if not has_subscription:
                return False
        return True

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
