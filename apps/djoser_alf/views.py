from django.conf import settings
from django.test import override_settings

from djoser.compat import get_user_email
from djoser.conf import settings as djoser_settings
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import SendEmailResetSerializer


class UserViewSet(DjoserUserViewSet):
    @action(["post"], detail=False)
    def reset_password(self, request, *args, **kwargs):
        serializer = SendEmailResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        users = serializer.get_users()

        for user in users:
            context = {"user": user}
            to = [get_user_email(user)]
            with override_settings(EMAIL_BACKEND=settings.DJMAIL_REAL_BACKEND):
                djoser_settings.EMAIL.password_reset(self.request, context).send(to)

        return Response(status=status.HTTP_204_NO_CONTENT)
