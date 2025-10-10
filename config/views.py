from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.db import connection

@api_view(['GET'])
def health_check(request):
    """
        check the health of the system (DB + App)
        later redis will be added
    """
    data = {
        "app": "OK",
        "database": "Unknown",
    }

    # Check DB conn
    try:
        connection.ensure_connection()
        data["database"] = "OK"
    except Exception as e:
        data["database"] = f"Error: {str(e)}"
    
    return Response(data,
                    status=status.HTTP_200_OK)