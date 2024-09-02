from rest_framework import views

from apps.facilities.models import FacilityUser

orig_perform_authentication = views.APIView.perform_authentication


def perform_authentication(self, request):
    orig_perform_authentication(self, request)
    if request.user.is_authenticated:
        try:
            facility_user = FacilityUser.objects.get(user=request.user)
            request.facility = facility_user.facility
            request.role = facility_user.role
        except FacilityUser.DoesNotExist:
            request.facility = None
            request.role = None


views.APIView.perform_authentication = perform_authentication
