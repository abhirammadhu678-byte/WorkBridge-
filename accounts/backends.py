from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import CustomUser

class EmailOrUsernameModelBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):

        if username is None:
            username = kwargs.get("username")

        user = CustomUser.objects.filter(
            Q(username=username) | Q(email=username)
        ).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None