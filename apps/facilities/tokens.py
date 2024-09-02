from urllib.parse import quote_plus, unquote_plus

from django.core.signing import BadSignature, Signer


class UserInviteTokenGenerator(object):
    key_salt = "user-invite-token-generator"

    def __init__(self):
        self.signer = Signer(salt=self.key_salt)

    def make_token(self, invite):
        token = self.signer.sign(invite.id)
        token = quote_plus(token)
        return token

    def check_token(self, invite, token):
        try:
            token = unquote_plus(token)
        except Exception:
            return False

        try:
            invite_id = int(self.signer.unsign(token))
        except BadSignature:
            return False

        return invite.id == invite_id
