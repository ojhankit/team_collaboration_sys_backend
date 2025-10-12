from django.urls import path
from .views import register_user, login_user, change_password, get_all_user
from .views_demo import demo_login
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('',get_all_user,name='get_users'),
    path('register/', register_user, name='register_user'),
    path('login/', login_user, name='login_user'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('change-password/', change_password, name='change-password'),
    path('demo/login/', demo_login, name='demo-login'),
]
