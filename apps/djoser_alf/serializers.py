from django.contrib.auth import get_user_model

from djoser.conf import settings
from djoser.serializers import SendEmailResetSerializer as DjoserSendEmailResetSerializer

User = get_user_model()


class SendEmailResetSerializer(DjoserSendEmailResetSerializer):
    def get_users(self, is_active=True):
        users = []

        qs = User._default_manager.filter(
            is_active=is_active,
            **{self.email_field: self.data.get(self.email_field, "")},
        )
        for user in qs:
            if user.has_usable_password():
                users.append(user)

        if users:
            return users

        if (
            settings.PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND
            or settings.USERNAME_RESET_SHOW_EMAIL_NOT_FOUND
        ):
            self.fail("email_not_found")
        return []
