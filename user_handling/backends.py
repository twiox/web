from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()


class EmailBackend(ModelBackend):
    """Login with username or email address, both case-insensitive.

    Several members can share an email address (e.g. siblings with their
    parents' address), so every matching account is tried with the password.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        candidates = UserModel.objects.filter(
            Q(username__iexact=username) | Q(email__iexact=username)
        ).order_by("id")
        for user in candidates:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        if not candidates:
            # hash anyway, so the response time doesn't reveal whether the account exists
            UserModel().set_password(password)
        return None
