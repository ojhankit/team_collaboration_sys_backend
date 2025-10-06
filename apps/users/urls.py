from django.urls import path
from .views import register_user, login_user
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', register_user, name='register-user'),
    path('login/', login_user, name='login-user'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
