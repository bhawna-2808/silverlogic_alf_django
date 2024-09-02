from rest_framework import exceptions
from timed_auth_token.authentication import TimedAuthTokenAuthentication

from ..facilities.models import TrainingsTimedAuthToken


class TrainingsTimedAuthTokenAuthentication(TimedAuthTokenAuthentication):
    model = TrainingsTimedAuthToken


class ApiKeyUrlAuthentication(TimedAuthTokenAuthentication):
    def authenticate(self, request):
        api_key = request.query_params.get("api_key")
        if not api_key:
            raise exceptions.AuthenticationFailed("You must provide an API key.")
        return self.authenticate_credentials(api_key)
