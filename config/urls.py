"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from .views import health_check

schema_view = get_schema_view(
    openapi.Info(
        title="Team Collaboration API",
        default_version='v1',
        description="""
        # 🚀 Team Collaboration API Documentation

        ## 🔐 Quick Start - Authentication

        ### Step 1: Test Users
        I have added a few users of all roles for testing purposes. Use the following credentials:

        **Admin**

        1. username: `Yag_admin` , **password:** `Yag@admin1`
        2. username: `yagadmin2` , **password:** `Yag@admin2`

        **Manager**

        1. username: `Yag_manager1` , **password:** `Yag@manager1`
        2. username: `Yag_manager2` , **password:** `Yag@manager2`

        **Employee**

        1. username: `Yag_employee1` , **password:** `Yag@employee1`
        2. username: `Yag_employee2` , **password:** `Yag@employee3`
        3. username: `Yag_employee3` , **password:** `Yag@employee2`

        ### Step 2: Get Your Token
        Send a POST request to `/api/users/login/` with JSON body:

        {
            "identifier": "<username>",
            "password": "<password>"
        }
                
        ### Step 3: Try It Out
        All protected endpoints will now work with your token automatically.
        
        ---
        
        ## 👥 Available Roles & Permissions
        
        | Role | Permissions |
        |------|-------------|
        | **Admin** | Full access to all resources |
        | **Manager** | Team management, task creation & assignment |
        | **Employee** | View and update assigned tasks |
        
        ---
        
        ## 📝 Important Notes
        
        - **Demo Mode**: Demo users have read-only access for safety
        - **Token Expiry**: Access tokens expire after a set time (check settings)
        - **Refresh Token**: Use `/api/auth/token/refresh/` to get a new access token
        - **Security**: Never share your tokens publicly
        
        ---
        
        ## 🔗 Useful Endpoints
        
        - Authentication: `/api/users/`
        - Tasks: `/api/tasks/`
        - Health Check: `/api/health/`
        
        ---
        
        ## 📚 API Features
        
        - ✅ JWT-based authentication
        - ✅ Role-based access control
        - ✅ Real-time notifications (WebSocket)
        - ✅ File uploads for tasks
        - ✅ Advanced filtering & pagination
        - ✅ RESTful design principles
        """,
        terms_of_service="https://www.yourapp.com/terms/",
        contact=openapi.Contact(
            name="API Support Team",
            email="support@yourapp.com",
            url="https://www.yourapp.com/support"
        ),
        license=openapi.License(
            name="MIT License",
            url="https://opensource.org/licenses/MIT"
        ),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[],  # Disable authentication for Swagger UI itself
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.users.urls')),
    path('api/tasks/', include('apps.tasks.urls')),
    path('api/health/', health_check, name='health_check'),

    # Swagger URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', 
            schema_view.without_ui(cache_timeout=0), 
            name='schema-json'),
    re_path(r'^swagger/$', 
            schema_view.with_ui('swagger', cache_timeout=0), 
            name='schema-swagger-ui'),
    re_path(r'^redoc/$', 
            schema_view.with_ui('redoc', cache_timeout=0), 
            name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)