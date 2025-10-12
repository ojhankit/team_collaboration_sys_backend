from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()

def get_or_create_demo_user(username, role):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": role.capitalize(),
            "last_name": "Demo",
            "date_of_birth": "2000-01-01",
            "role": role,
        }
    )

    return user

def generate_demo_token(username, role):
    user = get_or_create_demo_user(username, role)
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "role": user.role,
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def demo_login(request):
    """
    Public endpoint for generating demo JWT tokens for Swagger testing.
    """
    tokens = {
        "admin": generate_demo_token("demo_admin", "admin"),
        "manager": generate_demo_token("demo_manager", "manager"),
        "employee": generate_demo_token("demo_employee", "employee"),
    }

    return Response({
        "info": (
            "Use these tokens in Swagger via the 'Authorize' button.\n"
            "Paste them as 'Bearer <access_token>' to try different roles."
        ),
        "tokens": tokens
    })