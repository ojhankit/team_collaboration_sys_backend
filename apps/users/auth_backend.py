from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """
        Authenticate using email or username
    """
    def authenticate(self, request,
                     username=None,
                     password=None,
                     **kwargs):
        user = None
        if username is not None:
            username = kwargs.get('identifier')

        try:
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            return None

        if user and user.check_password(password):
            return user
        return None