"""additional authentication methods"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class EmailBackend(ModelBackend):
    """Allows authenticating using email for the username"""

    def authenticate(self, username=None, password=None):
        """Return the User objects with email=username if the password checks out. Otherwise return None."""

        if '@' in username:
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None
            else:
                if user.check_password(password):
                    return user
        return None
