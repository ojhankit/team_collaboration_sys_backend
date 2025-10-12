from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer
from .models import UserModel
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
import re
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
"""
Test api
"""
# @api_view(['GET'])
# def get_all_user(request):
#     users = UserModel.objects.all()
#     serializer = UserSerializer(users, many=True)
#     return Response(serializer.data)

@swagger_auto_schema(
    method='post',
    operation_summary="Register a new user",
    operation_description="Registers a new user with username, password, and role.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['username', 'password', 'first_name', 'last_name', 'date_of_birth'],
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, example="john_doe"),
            'password': openapi.Schema(type=openapi.TYPE_STRING, example="StrongPass@123"),
            'first_name': openapi.Schema(type=openapi.TYPE_STRING, example="John"),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING, example="Doe"),
            'date_of_birth': openapi.Schema(type=openapi.TYPE_STRING, example="2000-01-01"),
            'role': openapi.Schema(type=openapi.TYPE_STRING, enum=['admin', 'manager', 'employee']),
        }
    ),
    responses={
        201: "User registered successfully",
        400: "Validation error"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserSerializer(data = request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message" : "User registered successfully"
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    operation_summary="Login user",
    operation_description="Authenticate user using username and password, returns JWT tokens.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['identifier', 'password'],
        properties={
            'identifier': openapi.Schema(type=openapi.TYPE_STRING, example="john_doe"),
            'password': openapi.Schema(type=openapi.TYPE_STRING, example="StrongPass@123"),
        }
    ),
    responses={
        200: openapi.Response(
            description="Login successful",
            examples={
                "application/json": {
                    "access": "<access_token>",
                    "refresh": "<refresh_token>",
                    "username": "john_doe",
                    "email": "john@example.com"
                }
            }
        ),
        401: "Invalid credentials"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    identifier = request.data.get('identifier')
    password = request.data.get('password')

    if not identifier or not password:
        return Response(
            {'error': 'Both identifier and password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(request, username=identifier, password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'username': user.username,
            'email': user.email
        },status=status.HTTP_200_OK)
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

def blacklist_all_tokens(user):
    """ blacklist all active refresh tokens for a user """
    tokens = OutstandingToken.objects.filter(user=user)
    for token in tokens:
        try:
            BlacklistedToken.objects.get_or_create(token=token)
        except:
            pass

def validate_password_strength(password):
    """
    checks password strength
    1. atleast 6 chars
    2. containing uppercase, lowercase, number and special character
    """
    if len(password) < 6:
        return "password length is less than 6"
    if not re.search(r"[A-Z]", password):
        return "password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return "password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return "password must contain at least one number"
    if not re.search(r"[@$!%*?&]", password):
        return "password must contain at least one special character (@, $, !, %, *, ?, &)"
    return None

@swagger_auto_schema(
    method='post',
    operation_summary="Change password (Authenticated)",
    operation_description="Allows logged-in users to change their password. All old tokens are blacklisted.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['old_password', 'new_password'],
        properties={
            'old_password': openapi.Schema(type=openapi.TYPE_STRING, example="OldPass@123"),
            'new_password': openapi.Schema(type=openapi.TYPE_STRING, example="NewPass@123"),
        }
    ),
    responses={
        200: "Password changed successfully",
        400: "Invalid input or same password",
        401: "Unauthorized",
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Authenticated user password change
    input : {"old_password":"####","new_password":"@@@@"}
    """
    user = request.user
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")

    if not old_password or not new_password:
        return Response({
            "error":"Both old and new passwords are required"
        },status=status.HTTP_400_BAD_REQUEST)

    if not user.check_password(old_password):
        return Response(
            {"error":"old password is incorrect"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if old_password == new_password:
        return Response(
            {
                "error":"old and new password cannot be same"
            }, status=status.HTTP_400_BAD_REQUEST
        )
    
    validation_error = validate_password_strength(new_password)
    if validation_error:
        return Response({"error": validation_error}, status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(new_password)
    user.save()

    blacklist_all_tokens(user)
    refresh = RefreshToken.for_user(user)

    return Response({
        "message":"Password changed successfully, All previous session are logged out",
        "new_access": str(refresh.access_token),
        "new_refresh": str(refresh)
    }, status=status.HTTP_200_OK)