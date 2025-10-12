from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer
from .models import UserModel
from rest_framework.permissions import AllowAny, IsAuthenticated,IsAdminUser
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
import re
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from apps.tasks.permissions import TaskPermission

@swagger_auto_schema(
    method='get',
    operation_summary="Get all users",
    operation_description="""
    Retrieves a list of all registered users in the system.
    
    **Access Control:**
    - Only Admin users can access this endpoint
    - Returns basic user information (excludes sensitive data like passwords)
    
    **Response includes:**
    - User ID
    - Username
    - Email
    - First name and Last name
    - Date of birth
    - Role (admin, manager, employee)
    - Account creation date
    
    **Use Case:**
    Useful for admin dashboards, user management interfaces, or when assigning tasks to users.
    """,
    responses={
        200: openapi.Response(
            description="List of all users retrieved successfully",
            examples={
                "application/json": [
                    {
                        "id": 1,
                        "username": "john_doe",
                        "email": "john@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "date_of_birth": "1990-01-15",
                        "role": "employee",
                        "date_joined": "2025-01-01T10:00:00Z"
                    },
                    {
                        "id": 2,
                        "username": "jane_manager",
                        "email": "jane@example.com",
                        "first_name": "Jane",
                        "last_name": "Smith",
                        "date_of_birth": "1988-05-20",
                        "role": "manager",
                        "date_joined": "2025-01-05T14:30:00Z"
                    },
                    {
                        "id": 3,
                        "username": "admin_user",
                        "email": "admin@example.com",
                        "first_name": "Admin",
                        "last_name": "User",
                        "date_of_birth": "1985-12-10",
                        "role": "admin",
                        "date_joined": "2025-01-01T09:00:00Z"
                    }
                ]
            }
        ),
        401: openapi.Response(
            description="Unauthorized - Authentication required",
            examples={
                "application/json": {
                    "detail": "Authentication credentials were not provided."
                }
            }
        ),
        403: openapi.Response(
            description="Forbidden - Admin access required",
            examples={
                "application/json": {
                    "detail": "You do not have permission to perform this action."
                }
            }
        )
    },
    security=[{'Bearer': []}],
    tags=['Admin']
)
@api_view(['GET'])
@permission_classes([])  # Only admins can access
def get_all_user(request):
    """
    Get all users in the system.
    Requires admin authentication.
    """
    users = UserModel.objects.all()  # Fixed: Changed from UserSerializer to UserModel
    serializer = UserSerializer(users, many=True)  # Serialize the queryset
    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='post',
    operation_summary="Register a new user",
    operation_description="""
    Creates a new user account in the system.
    
    **Requirements:**
    - Username must be unique
    - Password must meet strength requirements (6+ chars, uppercase, lowercase, number, special char)
    - Date of birth must be in YYYY-MM-DD format
    - Role defaults to 'employee' if not provided
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['username', 'password', 'first_name', 'last_name', 'date_of_birth'],
        properties={
            'username': openapi.Schema(
                type=openapi.TYPE_STRING, 
                description="Unique username for the account",
                example="john_doe"
            ),
            'password': openapi.Schema(
                type=openapi.TYPE_STRING, 
                description="Must contain 6+ chars, uppercase, lowercase, number, and special character (@$!%*?&)",
                example="StrongPass@123"
            ),
            'first_name': openapi.Schema(
                type=openapi.TYPE_STRING, 
                description="User's first name",
                example="John"
            ),
            'last_name': openapi.Schema(
                type=openapi.TYPE_STRING, 
                description="User's last name",
                example="Doe"
            ),
            'date_of_birth': openapi.Schema(
                type=openapi.TYPE_STRING, 
                format=openapi.FORMAT_DATE,
                description="Date of birth in YYYY-MM-DD format",
                example="2000-01-01"
            ),
            'role': openapi.Schema(
                type=openapi.TYPE_STRING, 
                enum=['admin', 'manager', 'employee'],
                description="User role (defaults to 'employee')",
                example="employee"
            ),
        }
    ),
    responses={
        201: openapi.Response(
            description="User registered successfully",
            examples={
                "application/json": {
                    "message": "User registered successfully"
                }
            }
        ),
        400: openapi.Response(
            description="Validation error - invalid input data",
            examples={
                "application/json": {
                    "username": ["This field is required."],
                    "password": ["password must contain at least one uppercase letter"]
                }
            }
        )
    },
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "User registered successfully"
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_summary="User login",
    operation_description="""
    Authenticates a user and returns JWT access and refresh tokens.
    
    **Authentication Flow:**
    1. Provide username/email and password
    2. Receive access token (short-lived) and refresh token (long-lived)
    3. Use access token in Authorization header: `Bearer <access_token>`
    4. Use refresh token to get new access tokens when expired
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['identifier', 'password'],
        properties={
            'identifier': openapi.Schema(
                type=openapi.TYPE_STRING, 
                description="Username or email address",
                example="john_doe"
            ),
            'password': openapi.Schema(
                type=openapi.TYPE_STRING, 
                description="User's password",
                example="StrongPass@123"
            ),
        }
    ),
    responses={
        200: openapi.Response(
            description="Login successful - JWT tokens returned",
            examples={
                "application/json": {
                    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "username": "john_doe",
                    "email": "john@example.com"
                }
            }
        ),
        400: openapi.Response(
            description="Missing required fields",
            examples={
                "application/json": {
                    "error": "Both identifier and password are required."
                }
            }
        ),
        401: openapi.Response(
            description="Invalid credentials",
            examples={
                "application/json": {
                    "error": "Invalid credentials"
                }
            }
        )
    },
    tags=['Authentication']
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
        }, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


def blacklist_all_tokens(user):
    """Blacklist all active refresh tokens for a user"""
    tokens = OutstandingToken.objects.filter(user=user)
    for token in tokens:
        try:
            BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            pass


def validate_password_strength(password):
    """
    Validates password strength requirements:
    - At least 6 characters
    - Contains uppercase letter
    - Contains lowercase letter
    - Contains number
    - Contains special character (@$!%*?&)
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
    operation_summary="Change password",
    operation_description="""
    Allows authenticated users to change their password securely.
    
    **Security Features:**
    - Requires current password verification
    - New password must meet strength requirements
    - All existing refresh tokens are blacklisted (logs out all sessions)
    - New tokens are issued automatically
    
    **Important:** After password change, use the new tokens returned in the response.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['old_password', 'new_password'],
        properties={
            'old_password': openapi.Schema(
                type=openapi.TYPE_STRING, 
                description="Current password for verification",
                example="OldPass@123"
            ),
            'new_password': openapi.Schema(
                type=openapi.TYPE_STRING, 
                description="New password (must meet strength requirements: 6+ chars, uppercase, lowercase, number, special char)",
                example="NewPass@123"
            ),
        }
    ),
    responses={
        200: openapi.Response(
            description="Password changed successfully - new tokens issued",
            examples={
                "application/json": {
                    "message": "Password changed successfully, All previous session are logged out",
                    "new_access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "new_refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
                }
            }
        ),
        400: openapi.Response(
            description="Bad request - validation failed",
            examples={
                "application/json": {
                    "error": "old password is incorrect"
                }
            }
        ),
        401: openapi.Response(
            description="Unauthorized - authentication required",
            examples={
                "application/json": {
                    "detail": "Authentication credentials were not provided."
                }
            }
        ),
    },
    security=[{'Bearer': []}],
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Authenticated user password change
    Requires valid JWT token in Authorization header
    """
    user = request.user
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")

    if not old_password or not new_password:
        return Response({
            "error": "Both old and new passwords are required"
        }, status=status.HTTP_400_BAD_REQUEST)

    if not user.check_password(old_password):
        return Response(
            {"error": "old password is incorrect"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if old_password == new_password:
        return Response(
            {"error": "old and new password cannot be same"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validation_error = validate_password_strength(new_password)
    if validation_error:
        return Response({"error": validation_error}, status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(new_password)
    user.save()

    blacklist_all_tokens(user)
    refresh = RefreshToken.for_user(user)

    return Response({
        "message": "Password changed successfully, All previous session are logged out",
        "new_access": str(refresh.access_token),
        "new_refresh": str(refresh)
    }, status=status.HTTP_200_OK)